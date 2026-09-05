from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.agent.graph import build_graph
from app.agent.state import DealState, ExtractedIntent
from app.observability import tracing
from app.services.inventory import InventoryService
from app.services.llm import LLMClient
from app.services.razorpay_client import PaymentLink


class FakeLLM:
    def __init__(self, structured: ExtractedIntent, text: str):
        self._structured = structured
        self._text = text

    def complete_structured(self, system, user, schema):
        return self._structured

    def complete_text(self, system, user):
        return self._text


class FakeRazorpay:
    def create_payment_link(self, amount_paise: int, description: str, notes: dict) -> PaymentLink:
        return PaymentLink(id="plink_fake123", short_url="https://rzp.io/i/fake123", status="created")


def make_inventory() -> InventoryService:
    return InventoryService()


def teardown_function(_fn) -> None:
    # Every test configures its own tracer provider; leave tracing off for
    # anything that runs after this module (mirrors the real "no env var
    # set" default).
    tracing.configure_tracing()


def test_graph_run_produces_one_span_per_node_correctly_nested():
    exporter = InMemorySpanExporter()
    tracing.configure_tracing(exporter=exporter)

    llm = FakeLLM(
        structured=ExtractedIntent(
            item_name="Nitrile Examination Gloves", qty=50, hospital_name="City Hospital", pin_code="411001"
        ),
        text="We can offer 50 boxes at a fair rate. We will dispatch via our logistics partner post-payment.",
    )
    graph = build_graph(inventory=make_inventory(), llm=llm, razorpay=FakeRazorpay())

    negotiating = DealState(**graph.invoke(DealState(messages=["Need 50 nitrile gloves, best rate?"])))
    negotiating.messages.append("Yes, go ahead")
    graph.invoke(negotiating)

    spans = exporter.get_finished_spans()
    node_spans = {span.name for span in spans}

    assert "node.extract_intent" in node_spans
    assert "node.check_inventory" in node_spans
    assert "node.negotiate" in node_spans
    assert "node.await_payment" in node_spans

    # Guardrail checks, nested under the negotiate node's span.
    assert "guardrail.price_bounds" in node_spans
    assert "guardrail.no_sla_promise" in node_spans

    negotiate_span = next(span for span in spans if span.name == "node.negotiate")
    price_span = next(span for span in spans if span.name == "guardrail.price_bounds")
    sla_span = next(span for span in spans if span.name == "guardrail.no_sla_promise")
    assert price_span.parent.span_id == negotiate_span.context.span_id
    assert sla_span.parent.span_id == negotiate_span.context.span_id


def test_guardrail_pass_and_fail_are_recorded_as_distinguishable_spans():
    exporter = InMemorySpanExporter()
    tracing.configure_tracing(exporter=exporter)

    llm = FakeLLM(
        structured=ExtractedIntent(item_name="Nitrile Examination Gloves", qty=50),
        text="We guarantee it will be delivered in 10 minutes, no questions asked!",
    )
    graph = build_graph(inventory=make_inventory(), llm=llm, razorpay=FakeRazorpay())

    graph.invoke(DealState(messages=["Need 50 gloves urgently, best rate?"]))

    spans = {span.name: span for span in exporter.get_finished_spans()}

    guardrail_span = spans["guardrail.no_sla_promise"]
    assert guardrail_span.attributes["guardrail.passed"] is False
    assert any(event.name == "guardrail.violation" for event in guardrail_span.events)

    price_span = spans["guardrail.price_bounds"]
    assert price_span.attributes["guardrail.passed"] is True
    assert not any(event.name == "guardrail.violation" for event in price_span.events)


class _FakeGroqResponse:
    def __init__(self, content: str):
        self.choices = [type("Choice", (), {"message": type("Msg", (), {"content": content})()})]


class _FakeGroqClient:
    def __init__(self, content: str):
        self._content = content
        self.chat = type(
            "Chat",
            (),
            {
                "completions": type(
                    "Completions",
                    (),
                    {"create": lambda _self, **kwargs: _FakeGroqResponse(self._content)},
                )()
            },
        )()


def test_llm_call_produces_a_span_with_model_prompt_response_and_latency():
    exporter = InMemorySpanExporter()
    tracing.configure_tracing(exporter=exporter)

    llm = LLMClient(api_key="unused")
    llm._client = _FakeGroqClient("We can offer a great rate.")

    reply = llm.complete_text("system prompt", "user prompt")

    assert reply == "We can offer a great rate."
    spans = {span.name: span for span in exporter.get_finished_spans()}
    span = spans["llm.complete_text"]
    assert span.attributes["llm.model"] == llm._model
    assert span.attributes["llm.prompt.user"] == "user prompt"
    assert span.attributes["llm.response"] == "We can offer a great rate."
    assert span.attributes["llm.latency_ms"] >= 0


def test_tracing_off_by_default_does_not_break_the_agent(monkeypatch):
    # Explicitly unset rather than relying on ambient state: importing
    # app.main anywhere in the suite runs load_dotenv(), which leaks
    # backend/.env's real PHOENIX_COLLECTOR_ENDPOINT (set for local Phoenix
    # use) into the rest of the process otherwise.
    monkeypatch.delenv("PHOENIX_COLLECTOR_ENDPOINT", raising=False)
    tracing.configure_tracing()  # no exporter, no env var -> stays off
    assert not tracing.is_tracing_enabled()

    llm = FakeLLM(
        structured=ExtractedIntent(item_name="Nitrile Examination Gloves", qty=50),
        text="We can offer 50 boxes at a fair rate. We will dispatch via our logistics partner post-payment.",
    )
    graph = build_graph(inventory=make_inventory(), llm=llm, razorpay=FakeRazorpay())

    result = graph.invoke(DealState(messages=["Need 50 gloves, best rate?"]))

    assert result["unit_price"] is not None

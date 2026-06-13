import pytest
from uuid import uuid4
from app.domain.copilot import (
    AICFOCopilot, Conversation, Message, CopilotActionRecord,
    ReasoningChain, CopilotSuggestion, CopilotAction, ConversationRole,
    ConversationStatus, CopilotCapability, PriorityLevel,
)


class TestAICFOCopilot:
    def setup_method(self):
        self.tenant_id = "test-tenant"
        self.copilot = AICFOCopilot(self.tenant_id)
        self.user_id = uuid4()

    def test_process_query_analyze(self):
        msg, actions = self.copilot.process_query(
            self.user_id, "Analyze revenue trends for last quarter", {}
        )
        assert isinstance(msg, Message)
        assert msg.role == ConversationRole.ASSISTANT
        assert len(actions) > 0

    def test_process_query_forecast(self):
        msg, actions = self.copilot.process_query(
            self.user_id, "Forecast revenue for next quarter", {}
        )
        assert isinstance(msg, Message)

    def test_process_query_what_if(self):
        msg, actions = self.copilot.process_query(
            self.user_id, "What if we reduce staff by 10%?", {}
        )
        assert isinstance(msg, Message)

    def test_process_query_risk(self):
        msg, actions = self.copilot.process_query(
            self.user_id, "What are the biggest financial risks?", {}
        )
        assert isinstance(msg, Message)

    def test_process_query_recommendation(self):
        msg, actions = self.copilot.process_query(
            self.user_id, "Recommend cost reduction strategies", {}
        )
        assert isinstance(msg, Message)

    def test_multi_step_reasoning(self):
        chain = self.copilot.multi_step_reasoning(
            "Why is revenue declining?", {}
        )
        assert isinstance(chain, ReasoningChain)
        assert len(chain.steps) >= 3
        assert chain.confidence > 0

    def test_generate_suggestions(self):
        suggestions = self.copilot.generate_suggestions(self.user_id, {})
        assert isinstance(suggestions, list)
        for s in suggestions:
            assert isinstance(s, CopilotSuggestion)
            assert s.title is not None

    def test_explain_reasoning(self):
        msg, actions = self.copilot.process_query(self.user_id, "Analyze something", {})
        if actions:
            reasoning = self.copilot.explain_reasoning(actions[0].id)
            assert isinstance(reasoning, list)

    def test_get_conversations(self):
        # Create a conversation by processing a query
        self.copilot.process_query(self.user_id, "Hello", {})
        convos = self.copilot.get_conversations(self.tenant_id, self.user_id, limit=10)
        assert isinstance(convos, list)

    def test_get_conversation(self):
        self.copilot.process_query(self.user_id, "Test query", {})
        convos = self.copilot.get_conversations(self.tenant_id, self.user_id, limit=1)
        if convos:
            result = self.copilot.get_conversation(self.tenant_id, convos[0].id)
            assert result is not None

    def test_archive_conversation(self):
        self.copilot.process_query(self.user_id, "Archive me", {})
        convos = self.copilot.get_conversations(self.tenant_id, self.user_id, limit=1)
        if convos:
            archived = self.copilot.archive_conversation(self.tenant_id, convos[0].id)
            assert archived.status == ConversationStatus.ARCHIVED

    def test_copilot_action_enum(self):
        assert len(CopilotAction) == 15

    def test_reasoning_step_enum(self):
        from app.domain.copilot import ReasoningStep
        assert len(ReasoningStep) == 8

    def test_copilot_capability_enum(self):
        assert len(CopilotCapability) == 15

    def test_conversation_status_enum(self):
        assert len(ConversationStatus) == 2

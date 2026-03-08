"""
Chat router — the main /chat endpoint that ties the LLM agent, service
router, and conversation history together.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.bot.agent import query_llm, parse_action
from app.bot.router import execute_action

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation: list[dict] = []  # previous turns: [{"role": "...", "content": "..."}]


class ChatResponse(BaseModel):
    reply: str
    service_result: dict | None = None
    escalated: bool = False


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Main conversational endpoint.
    1. Forward the conversation + new message to the LLM.
    2. If the LLM outputs a structured action, execute the service.
    3. Return the final reply to the frontend.
    """
    # Build conversation for the LLM
    history = list(req.conversation)
    history.append({"role": "user", "content": req.message})

    # Step 1 — Ask the LLM
    llm_reply = await query_llm(history)

    # Step 2 — Check if the LLM returned a tool-call action
    action = parse_action(llm_reply)

    if action:
        action_name = action.get("action", "")
        entities = action.get("entities", {})
        result = await execute_action(action_name, entities)

        if result.get("success"):
            # Step 3a — We got data; ask the LLM to compose a friendly reply
            follow_up = (
                f"Here is the result from the {result.get('service', 'service')} lookup:\n\n"
                f"{result['summary']}\n\n"
                "Please present this information clearly to the user in a friendly, "
                "easy-to-understand format. Include the policy reference."
            )
            history.append({"role": "assistant", "content": llm_reply})
            history.append({"role": "user", "content": follow_up})
            final_reply = await query_llm(history)
            return ChatResponse(reply=final_reply, service_result=result.get("data"))
        else:
            # Service call failed — relay the error message
            return ChatResponse(reply=result.get("message", "Something went wrong."))

    # Step 3b — No action detected; the LLM's reply IS the response
    # Check for escalation keywords
    escalation_keywords = ["human officer", "escalate", "connect you to", "transfer"]
    escalated = any(kw in llm_reply.lower() for kw in escalation_keywords)

    return ChatResponse(reply=llm_reply, escalated=escalated)

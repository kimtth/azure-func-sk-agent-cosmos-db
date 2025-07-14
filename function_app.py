import logging
import json
import uuid
import azure.functions as func
from func_sk_agent import process_request

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.function_name(name="func_sk_cosmos_db")
@app.route(route="chat", auth_level=func.AuthLevel.ANONYMOUS)
async def func_sk_cosmos_db(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing a request")
    try:
        # Get session ID from query parameters or generate a new one
        session = req.params.get("sessionId") or str(uuid.uuid4())
        # Get request body
        # Support both GET and POST: GET uses query parameters, POST uses JSON body
        body = req.get_json() if req.get_body() else {}
        # Get user message
        user_msg = req.params.get("user_msg") or body.get("user_msg", "")

        # Validate user message
        if not user_msg:
            return func.HttpResponse("You must provide a user message.", status_code=400)

        # Process the request to sk_agent
        response = await process_request(session, user_msg)

        # Return the response as JSON
        return func.HttpResponse(
            body=json.dumps({"resp": response}, ensure_ascii=False),
            mimetype="application/json",
            charset="utf-8",
        )
    except Exception as e:
        logging.error(f"An error occurred while processing the request: {e}")
        return func.HttpResponse("Internal Server Error", status_code=500)
from typing import Dict, Any, Optional, List
import os

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from phi.tools import Toolkit, tool
from phi.utils.log import logger

class TwilioTools(Toolkit):
    """Tools for interacting with the Twilio API."""

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.account_sid = account_sid or os.environ.get("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.environ.get("TWILIO_AUTH_TOKEN")
        self.from_number = from_number or os.environ.get("TWILIO_FROM_NUMBER")

        if not self.account_sid or not self.auth_token:
            raise ValueError(
                "Twilio account_sid and auth_token are required. "
                "Please set them in the environment variables or pass them as arguments."
            )

        self.client = Client(self.account_sid, self.auth_token)

        self.register(self.send_sms)
        self.register(self.get_call_details)
        self.register(self.list_messages)

    @tool
    def send_sms(self, to: str, body: str, from_: Optional[str] = None) -> str:
        """Send an SMS message using Twilio.

        Args:
            to: The phone number to send the message to (E.164 format, e.g. +1234567890)
            body: The message content to send
            from_: Optional override of the default from number (E.164 format)

        Returns:
            str: The message SID if successful

        Raises:
            ValueError: If the from number is not set or if there's a Twilio error
        """
        logger.info(f"Sending SMS to {to}")
        from_ = from_ or self.from_number
        if not from_:
            raise ValueError("Twilio from_number not set")

        try:
            message = self.client.messages.create(
                to=to,
                from_=from_,
                body=body,
            )
            return f"Message sent successfully. SID: {message.sid}"
        except TwilioRestException as e:
            error_msg = f"Error sending SMS: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    @tool
    def get_call_details(self, call_sid: str) -> Dict[str, Any]:
        """Get details about a specific Twilio call.

        Args:
            call_sid: The unique identifier of the call

        Returns:
            Dict containing call details including status, duration, etc.
        """
        logger.info(f"Getting call details for {call_sid}")
        try:
            call = self.client.calls(call_sid).fetch()
            return {
                "sid": call.sid,
                "from": call.from_formatted,
                "to": call.to_formatted,
                "status": call.status,
                "start_time": str(call.start_time),
                "end_time": str(call.end_time),
                "duration": call.duration,
                "price": call.price,
                "direction": call.direction,
            }
        except TwilioRestException as e:
            error_msg = f"Error retrieving call details: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    @tool
    def list_messages(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get a list of recent messages.

        Args:
            limit: Maximum number of messages to retrieve (default: 20)

        Returns:
            List of dictionaries containing message details
        """
        logger.info(f"Listing last {limit} messages")
        try:
            messages = self.client.messages.list(limit=limit)
            return [
                {
                    "sid": msg.sid,
                    "from": msg.from_formatted,
                    "to": msg.to_formatted,
                    "body": msg.body,
                    "status": msg.status,
                    "date_sent": str(msg.date_sent),
                    "direction": msg.direction,
                }
                for msg in messages
            ]
        except TwilioRestException as e:
            error_msg = f"Error retrieving message list: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) 
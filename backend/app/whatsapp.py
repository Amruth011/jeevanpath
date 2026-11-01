from dataclasses import dataclass

import httpx


class WhatsAppConfigurationError(RuntimeError):
    pass


class WhatsAppError(RuntimeError):
    pass


@dataclass
class WhatsAppCloud:
    access_token: str | None
    phone_number_id: str | None
    graph_version: str = "v21.0"

    @property
    def configured(self) -> bool:
        return bool(self.access_token and self.phone_number_id)

    def _check_config(self) -> None:
        if not self.configured:
            raise WhatsAppConfigurationError(
                "WhatsApp Cloud configuration is missing. Set the access token and phone number ID."
            )

    @property
    def _base_url(self) -> str:
        return f"https://graph.facebook.com/{self.graph_version}"

    async def download_media(self, media_id: str) -> tuple[bytes, str]:
        self._check_config()
        headers = {"Authorization": f"Bearer {self.access_token}"}
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                metadata = await client.get(f"{self._base_url}/{media_id}", headers=headers)
                metadata.raise_for_status()
                media_url = metadata.json().get("url")
                if not isinstance(media_url, str) or not media_url:
                    raise WhatsAppError("WhatsApp media response did not contain a download URL.")
                audio = await client.get(media_url, headers=headers)
                audio.raise_for_status()
                return audio.content, audio.headers.get("content-type", "audio/ogg")
        except WhatsAppError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise WhatsAppError(f"WhatsApp media download failed: {exc}") from exc

    async def send_text(self, recipient: str, text: str) -> None:
        await self._send(recipient, {"type": "text", "text": {"body": text}})

    async def send_audio(self, recipient: str, audio: bytes, content_type: str = "audio/wav") -> None:
        self._check_config()
        headers = {"Authorization": f"Bearer {self.access_token}"}
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                media = await client.post(
                    f"{self._base_url}/{self.phone_number_id}/media",
                    headers=headers,
                    files={"file": ("reply.wav", audio, content_type)},
                    data={"messaging_product": "whatsapp", "type": content_type},
                )
                media.raise_for_status()
                media_id = media.json().get("id")
                if not isinstance(media_id, str) or not media_id:
                    raise WhatsAppError("WhatsApp upload response did not contain a media ID.")
                await self._send(recipient, {"type": "audio", "audio": {"id": media_id}})
        except WhatsAppError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise WhatsAppError(f"WhatsApp audio send failed: {exc}") from exc

    async def _send(self, recipient: str, message: dict) -> None:
        self._check_config()
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {"messaging_product": "whatsapp", "to": recipient, **message}
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self._base_url}/{self.phone_number_id}/messages",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise WhatsAppError(f"WhatsApp message send failed: {exc}") from exc

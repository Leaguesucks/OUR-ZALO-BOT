# Architecture

`CLI → ZaloClient.get_update → Update → handler → ZaloClient.send_message`

The client calls `POST https://bot-api.zaloplatforms.com/bot<TOKEN>/<method>`.
`getUpdates` sends `{"timeout": "30"}` and parses **one event object** from `result`.
There is no offset, update-id cursor, or batch parameter in the documented Zalo interface.
Unknown event fields are ignored; events without messages can be passed to custom handlers.

References checked November 5, 2026:

- [getUpdates](https://docs.zaloplatforms.com/docs/BOT/apis/getUpdates)
- [sendMessage](https://docs.zaloplatforms.com/docs/BOT/apis/sendMessage)
- [getMe](https://docs.zaloplatforms.com/docs/BOT/apis/getMe)
- [deleteWebhook](https://docs.zaloplatforms.com/docs/BOT/apis/deleteWebhook)

`handlers.py` contains the initial application behavior. Add commands there, or inject an
async callable into `run_polling(..., handler=...)`. Put integrations and domain services
in separate modules as they become necessary. Handlers run sequentially; slow operations
delay the next poll. Async I/O should be awaited; blocking work needs a worker or thread.

## Failure and delivery behavior

- Polling transport failures, 429, and 5xx responses use capped exponential backoff with
  jitter. Numeric HTTP `Retry-After` is honored up to 300 seconds, even above the backoff cap.
- A polling 408 is treated as an idle cycle; this defensive compatibility behavior should
  be verified against your live bot. A null result is also treated as idle.
- Other API failures or malformed response schemas stop polling with a nonzero exit status.
  This makes invalid credentials and incompatible API changes visible.
- Completed event/message/chat identities are remembered for up to 1,000 messages in memory.
  This is best-effort duplicate suppression and resets on restart.
- Handler exceptions are logged by class and polling continues. Failed events are not marked
  completed, but the server may never return them again. There is no local requeue or dead-letter
  storage. Add a durable inbox and idempotent business actions before relying on delivery.
- Outbound sends are not retried automatically. A network failure after acceptance can make
  delivery ambiguous. Retrying a handler can duplicate earlier sends or external side effects.
- Cancellation interrupts polls/backoff/handlers and closes the HTTP client. An interrupted
  event is not guaranteed to be redelivered.

Tests simulate the wire format and failure paths without contacting Zalo. They do not prove
live credentials, platform quotas, event retention, or delivery guarantees. No exactly-once
or durable processing guarantee is claimed by this starter.

from rastro.common.domain.errors import BaseError


class NoteRejectedError(BaseError):
    code = "common_sample.note_rejected"

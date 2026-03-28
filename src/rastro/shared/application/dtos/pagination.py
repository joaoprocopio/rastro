from dataclasses import dataclass


@dataclass(frozen=True)
class PaginationInput:
    page: int = 1
    per_page: int = 20

    def __post_init__(self):
        if self.page < 1:
            raise ValueError("Page must be at least 1")
        if self.per_page < 1 or self.per_page > 100:
            raise ValueError("Page", "per_page must be between 1 and 100")


@dataclass(frozen=True)
class PaginationOutput:
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


@dataclass(frozen=True)
class PaginatedResponse:
    items: list
    pagination: PaginationOutput

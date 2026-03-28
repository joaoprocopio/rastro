from dataclasses import dataclass


@dataclass(frozen=True)
class PaginationParams:
    page: int = 1
    per_page: int = 20

    def __post_init__(self):
        if self.page < 1:
            raise ValueError("Page must be at least 1")
        if self.per_page < 1 or self.per_page > 100:
            raise ValueError("per_page must be between 1 and 100")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        return self.per_page

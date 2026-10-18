import pytest

from rastro.common.tests.sample.models import Post, Status


@pytest.mark.django_db
def test_sets_created_at_on_creation() -> None:
    post = Post.objects.create(status=Status.DRAFT)

    assert post.created_at is not None
    assert post.updated_at >= post.created_at


@pytest.mark.django_db
def test_updates_updated_at_on_save() -> None:
    post = Post.objects.create(status=Status.DRAFT)
    first_updated_at = post.updated_at

    post.status = Status.PUBLISHED
    post.save()

    assert post.updated_at > first_updated_at
    assert post.created_at < post.updated_at

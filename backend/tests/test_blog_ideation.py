"""Backend tests for Blog Ideation Tool APIs"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealth:
    def test_health(self):
        res = requests.get(f"{BASE_URL}/api/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

class TestSourceAPIs:
    def test_repo_sources_returns_data(self):
        res = requests.get(f"{BASE_URL}/api/sources/repo", timeout=15)
        assert res.status_code == 200
        data = res.json()
        assert "sources" in data
        assert "count" in data
        print(f"Repo sources count: {data['count']}")

    def test_repo_sources_returns_30(self):
        res = requests.get(f"{BASE_URL}/api/sources/repo", timeout=15)
        assert res.status_code == 200
        data = res.json()
        assert data['count'] >= 20, f"Expected ~30 repo sources, got {data['count']}"

    def test_repo_source_fields(self):
        res = requests.get(f"{BASE_URL}/api/sources/repo", timeout=15)
        data = res.json()
        if data['sources']:
            src = data['sources'][0]
            assert 'id' in src
            assert 'type' in src
            assert src['type'] == 'repo'
            assert 'title' in src
            assert 'tags' in src

    def test_arxiv_sources(self):
        res = requests.get(f"{BASE_URL}/api/sources/arxiv", timeout=30)
        assert res.status_code == 200
        data = res.json()
        assert "sources" in data
        print(f"ArXiv sources count: {data['count']}")

    def test_rss_sources(self):
        res = requests.get(f"{BASE_URL}/api/sources/rss", timeout=30)
        assert res.status_code == 200
        data = res.json()
        assert "sources" in data
        print(f"RSS sources count: {data['count']}")

    def test_all_sources(self):
        res = requests.get(f"{BASE_URL}/api/sources/all", timeout=30)
        assert res.status_code == 200
        data = res.json()
        assert "sources" in data
        assert "total" in data
        assert data['total'] > 0
        print(f"Total sources: {data['total']}")


class TestDraftsCRUD:
    draft_id = None

    def test_list_drafts_empty_or_existing(self):
        res = requests.get(f"{BASE_URL}/api/drafts")
        assert res.status_code == 200
        data = res.json()
        assert "drafts" in data
        assert isinstance(data['drafts'], list)

    def test_save_draft(self):
        payload = {
            "title": "TEST_Blog Ideas on FHE",
            "content": "## Blog Idea 1\nFHE for ML inference\n",
            "mode": "ideas",
            "source_ids": ["repo-day-1"],
            "tags": ["fhe", "ppml"]
        }
        res = requests.post(f"{BASE_URL}/api/drafts", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "id" in data
        TestDraftsCRUD.draft_id = data['id']
        print(f"Created draft id: {data['id']}")

    def test_get_draft(self):
        if not TestDraftsCRUD.draft_id:
            pytest.skip("No draft_id from save test")
        res = requests.get(f"{BASE_URL}/api/drafts/{TestDraftsCRUD.draft_id}")
        assert res.status_code == 200
        data = res.json()
        assert data['title'] == "TEST_Blog Ideas on FHE"
        assert data['mode'] == "ideas"

    def test_update_draft(self):
        if not TestDraftsCRUD.draft_id:
            pytest.skip("No draft_id from save test")
        res = requests.put(
            f"{BASE_URL}/api/drafts/{TestDraftsCRUD.draft_id}",
            json={"title": "TEST_Updated Blog Ideas on FHE"}
        )
        assert res.status_code == 200

        # Verify update persisted
        get_res = requests.get(f"{BASE_URL}/api/drafts/{TestDraftsCRUD.draft_id}")
        assert get_res.json()['title'] == "TEST_Updated Blog Ideas on FHE"

    def test_delete_draft(self):
        if not TestDraftsCRUD.draft_id:
            pytest.skip("No draft_id from save test")
        res = requests.delete(f"{BASE_URL}/api/drafts/{TestDraftsCRUD.draft_id}")
        assert res.status_code == 200

        # Verify deleted
        get_res = requests.get(f"{BASE_URL}/api/drafts/{TestDraftsCRUD.draft_id}")
        assert get_res.status_code == 404


class TestIdeationValidation:
    def test_ideate_no_sources_returns_400(self):
        res = requests.post(f"{BASE_URL}/api/ideate", json={
            "source_texts": [],
            "source_titles": [],
            "mode": "ideas"
        })
        assert res.status_code == 400

    def test_ideate_invalid_mode_returns_400(self):
        res = requests.post(f"{BASE_URL}/api/ideate", json={
            "source_texts": ["some text"],
            "source_titles": ["some title"],
            "mode": "invalid_mode"
        })
        assert res.status_code == 400

    def test_ideate_ideas_mode(self):
        """Test actual AI generation with ideas mode (cheapest)"""
        res = requests.post(f"{BASE_URL}/api/ideate", json={
            "source_texts": ["Federated Learning with differential privacy using Opacus library. Day 1 progress."],
            "source_titles": ["Day 1: Federated Learning Introduction"],
            "mode": "ideas"
        }, timeout=60)
        assert res.status_code == 200
        data = res.json()
        assert "content" in data
        assert len(data['content']) > 50
        assert data['mode'] == "ideas"
        print(f"Generated content length: {len(data['content'])}")

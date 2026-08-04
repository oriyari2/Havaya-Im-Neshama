from unittest import TestCase
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
from desktop_client.app.features.activities.service import ActivityService
from desktop_client.app.media_config import MAX_PREVIEW_DOWNLOAD_BYTES, MAX_UPLOAD_SIZE_BYTES

class ActivityServiceTests(TestCase):
    def setUp(self): self.api=Mock(); self.service=ActivityService(self.api)
    def test_list_and_detail(self):
        filters={"search":"x","target_audience":"y","season":"s","tag":"t","is_active":False,"limit":25,"offset":50}; self.service.list_activities(filters); self.api.get.assert_called_with("/activities",filters); self.service.activity("a1"); self.api.get.assert_called_with("/activities/a1")
    def test_mutations(self):
        self.service.create_activity({"name":"A"}); self.api.post.assert_called_with("/activities",{"name":"A"}); self.service.update_activity("a1",{"name":"B"}); self.api.put.assert_called_with("/activities/a1",{"name":"B"}); self.service.deactivate_activity("a1"); self.api.delete.assert_called_with("/activities/a1"); self.service.reactivate_activity("a1"); self.api.put.assert_called_with("/activities/a1",{"is_active":True})
    def test_image_endpoints_and_preview_limit(self):
        self.service.delete_image("a1","i1"); self.api.delete.assert_called_with("/activities/a1/images/i1")
        self.service.preview_bytes("https://cdn.example/i1"); self.api.get_public_bytes.assert_called_with("https://cdn.example/i1",max_bytes=MAX_PREVIEW_DOWNLOAD_BYTES)
    def test_upload_validates_and_sends_supported_file(self):
        with TemporaryDirectory() as directory:
            path=Path(directory)/"פלאייר.PNG"; path.write_bytes(b"png")
            self.service.upload_image("a1",str(path))
        self.api.post_multipart.assert_called_once_with("/activities/a1/images",field_name="file",filename="פלאייר.PNG",content_type="image/png",file_bytes=b"png")
    def test_upload_rejects_missing_empty_unsupported_and_oversized(self):
        with TemporaryDirectory() as directory:
            base=Path(directory)
            for name,content in (("empty.png",b""),("bad.gif",b"x")):
                path=base/name; path.write_bytes(content)
                with self.assertRaises(ValueError): self.service.upload_image("a1",str(path))
            large=base/"large.jpg"
            with large.open("wb") as stream: stream.truncate(MAX_UPLOAD_SIZE_BYTES+1)
            with self.assertRaises(ValueError): self.service.upload_image("a1",str(large))
            with self.assertRaises(ValueError): self.service.upload_image("a1",str(base/"missing.png"))
        self.api.post_multipart.assert_not_called()
    def test_exact_upload_limit_succeeds_and_one_byte_above_fails(self):
        with TemporaryDirectory() as directory:
            exact=Path(directory)/"exact.png"; exact.write_bytes(b"x"*MAX_UPLOAD_SIZE_BYTES); self.service.upload_image("a1",str(exact)); self.assertEqual(len(self.api.post_multipart.call_args.kwargs["file_bytes"]),MAX_UPLOAD_SIZE_BYTES)
            above=Path(directory)/"above.png"; above.write_bytes(b"x");
            with patch.object(Path,"stat",return_value=Mock(st_mode=exact.stat().st_mode,st_size=MAX_UPLOAD_SIZE_BYTES+1)):
                with self.assertRaises(ValueError): self.service.upload_image("a1",str(above))
        self.assertEqual(self.api.post_multipart.call_count,1)
    def test_stat_and_read_failures_are_safe(self):
        with patch.object(Path,"stat",side_effect=PermissionError("secret path")):
            with self.assertRaises(ValueError) as raised: self.service.upload_image("a1","secret.png")
        self.assertNotIn("secret",str(raised.exception)); self.api.post_multipart.assert_not_called()
        with TemporaryDirectory() as directory:
            path=Path(directory)/"image.png"; path.write_bytes(b"x")
            with patch.object(Path,"read_bytes",side_effect=OSError("raw os details")):
                with self.assertRaises(ValueError) as raised: self.service.upload_image("a1",str(path))
        self.assertNotIn("raw os",str(raised.exception)); self.api.post_multipart.assert_not_called()

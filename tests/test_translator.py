import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

if sys.platform == 'win32':
    import translator
else:
    translator = None


@unittest.skipUnless(sys.platform == 'win32', 'Windows-only application')
class LanguageTests(unittest.TestCase):
    def test_english(self):
        self.assertEqual(translator.detect_lang('Hello, world!'), 'en')

    def test_chinese(self):
        self.assertEqual(translator.detect_lang('\u4f60\u597d'), 'zh')

    def test_mixed_text_uses_chinese(self):
        self.assertEqual(translator.detect_lang('Hello \u4f60\u597d'), 'zh')

    def test_empty_text(self):
        self.assertEqual(translator.detect_lang(''), 'en')


@unittest.skipUnless(sys.platform == 'win32', 'Windows-only application')
class ConfigTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.config = Path(directory.name) / 'translator_config.ini'
        config_patch = patch.object(translator, 'CONFIG_FILE', str(self.config))
        config_patch.start()
        self.addCleanup(config_patch.stop)

    def test_missing_config(self):
        self.assertEqual(translator.load_api_key(), '')

    def test_empty_config(self):
        self.config.touch()
        self.assertEqual(translator.load_api_key(), '')

    def test_config_round_trip(self):
        translator.save_api_key('example.test-only')
        self.assertEqual(translator.load_api_key(), 'example.test-only')

    def test_source_directory(self):
        with patch.object(sys, 'frozen', False, create=True):
            self.assertEqual(
                translator._app_dir(),
                os.path.dirname(os.path.abspath(translator.__file__)),
            )

    def test_executable_directory(self):
        with patch.object(sys, 'frozen', True, create=True):
            self.assertEqual(
                translator._app_dir(), os.path.dirname(sys.executable),
            )


@unittest.skipUnless(sys.platform == 'win32', 'Windows-only application')
class TranslationTests(unittest.TestCase):
    def setUp(self):
        api_patch = patch.object(translator, 'API_KEY', 'example.test-only')
        api_patch.start()
        self.addCleanup(api_patch.stop)
        request_patch = patch.object(translator.requests, 'post')
        self.post = request_patch.start()
        self.addCleanup(request_patch.stop)
        self.response = Mock()
        self.response.json.return_value = {
            'choices': [{'message': {'content': '  translated text  '}}],
        }
        self.post.return_value = self.response

    def test_english_request(self):
        self.assertEqual(translator.translate('Hello'), 'translated text')
        self.response.raise_for_status.assert_called_once_with()
        args, kwargs = self.post.call_args
        self.assertEqual(args[0], 'https://open.bigmodel.cn/api/paas/v4/chat/completions')
        self.assertEqual(kwargs['headers']['Authorization'], 'Bearer example.test-only')
        self.assertEqual(kwargs['json']['model'], translator.MODEL)
        self.assertIn('\u82f1\u6587\u7ffb\u8bd1\u6210\u4e2d\u6587', kwargs['json']['messages'][0]['content'])
        self.assertEqual(kwargs['timeout'], 30)

    def test_chinese_request(self):
        translator.translate('\u4f60\u597d')
        prompt = self.post.call_args.kwargs['json']['messages'][0]['content']
        self.assertIn('\u4e2d\u6587\u7ffb\u8bd1\u6210\u82f1\u6587', prompt)

    def test_network_failure(self):
        self.post.side_effect = translator.requests.Timeout('test timeout')
        self.assertEqual(translator.translate('Hello'), '[Error: test timeout]')

    def test_http_failure(self):
        self.response.raise_for_status.side_effect = translator.requests.HTTPError('test HTTP error')
        self.assertEqual(translator.translate('Hello'), '[Error: test HTTP error]')


@unittest.skipUnless(sys.platform == 'win32', 'Windows-only application')
class ShortcutTests(unittest.TestCase):
    def setUp(self):
        state_patch = patch.multiple(
            translator,
            _simulating=False,
            _ctrl_pressed=False,
            _ctrl_press_time=0.0,
            _last_ctrl_click_t=0.0,
            _other_key_in_ctrl=False,
        )
        state_patch.start()
        self.addCleanup(state_patch.stop)
        thread_patch = patch.object(translator.threading, 'Thread')
        self.thread = thread_patch.start()
        self.addCleanup(thread_patch.stop)

    def test_double_ctrl_starts_worker(self):
        with patch.object(translator.time, 'time', return_value=100.0):
            for _ in range(2):
                translator.on_key_press(translator.pynkb.Key.ctrl_l)
                translator.on_key_release(translator.pynkb.Key.ctrl_l)
        self.thread.assert_called_once_with(target=translator.translation_worker, daemon=True)
        self.thread.return_value.start.assert_called_once_with()

    def test_ctrl_c_does_not_start_worker(self):
        with patch.object(translator.time, 'time', return_value=100.0):
            translator.on_key_press(translator.pynkb.Key.ctrl_l)
            translator.on_key_press(translator.pynkb.KeyCode.from_char('c'))
            translator.on_key_release(translator.pynkb.Key.ctrl_l)
        self.thread.assert_not_called()

    def test_long_hold_does_not_start_worker(self):
        with patch.object(translator.time, 'time', side_effect=[100.0, 101.0]):
            translator.on_key_press(translator.pynkb.Key.ctrl_l)
            translator.on_key_release(translator.pynkb.Key.ctrl_l)
        self.thread.assert_not_called()

    def test_simulated_input_is_ignored(self):
        with patch.object(translator, '_simulating', True):
            translator.on_key_press(translator.pynkb.Key.ctrl_l)
            translator.on_key_release(translator.pynkb.Key.ctrl_l)
        self.assertFalse(translator._ctrl_pressed)
        self.thread.assert_not_called()


if __name__ == '__main__':
    unittest.main()

import mock

from tornado import testing

from zk_monitor.alerts import email


class TestEmailAlerter(testing.AsyncTestCase):
    def setUp(self):
        super(TestEmailAlerter, self).setUp()
        self.mocked_cs = mock.MagicMock()
        self.mocked_lock = mock.MagicMock()
        self.mocked_cs.getLock.return_value = self.mocked_lock
        self.alerter = email.EmailAlerter()

    @mock.patch('tornadomail.backends.smtp.EmailBackend')
    @mock.patch('zk_monitor.alerts.email.EmailAlert')
    def testAlert(self, mocked_alert, mocked_backend):
        backend_instance = mocked_backend.return_value

        self.alerter._alert('/foo', 'Broken',
                            'Unit Test Message', 'unit@test.com')
        mocked_alert.assert_called_with(
            subject='Warning! /foo has an alert!',
            body='Unit Test Message\n/foo is in the Broken state.',
            email='unit@test.com',
            conn=backend_instance)

    @mock.patch('tornadomail.backends.smtp.EmailBackend')
    @mock.patch('zk_monitor.alerts.email.EmailAlert')
    def testAlertMany(self, mocked_alert, mocked_backend):
        backend_instance = mocked_backend.return_value

        self.alerter._alert('/foo', 'Broken',
                            'Unit Test Message', 'unit@test.com, u2@test.com')
        mocked_alert.assert_any_call(
            subject='Warning! /foo has an alert!',
            body='Unit Test Message\n/foo is in the Broken state.',
            email='unit@test.com',
            conn=backend_instance)
        mocked_alert.assert_any_call(
            subject='Warning! /foo has an alert!',
            body='Unit Test Message\n/foo is in the Broken state.',
            email='u2@test.com',
            conn=backend_instance)

    @testing.gen_test
    def testNotValid(self):
        # _alert() should exit if "params" is not defined.
        res = yield self.alerter._alert(
            '/foo', 'Broken', 'Unit Test Message', {})
        self.assertEquals(None, res)

    def testSingleBackend(self):
        once = self.alerter._mail_backend
        twice = self.alerter._mail_backend
        self.assertEqual(once, twice)


class TestEmailAlert(testing.AsyncTestCase):
    def setUp(self):
        super(TestEmailAlert, self).setUp()
        self.msg = 'unit test msg'
        self.body = 'unit test body'
        self.email = 'unit@test.com'
        self.conn = mock.MagicMock()

    @mock.patch('tornadomail.message.EmailMessage')
    def testInit(self, mocked_message):
        email.EmailAlert(self.msg, self.body, None, self.conn)
        email.EmailAlert(self.msg, self.body, self.email, self.conn)
        mocked_message.assert_called_with(
            subject=self.msg,
            body=self.body,
            to=self.email,
            from_email='zk_monitor',
            connection=self.conn)

    @mock.patch('tornadomail.message.EmailMessage')
    def testAlertSent(self, mocked_message):
        alert = email.EmailAlert(self.msg, self.body, self.email, self.conn)
        self.assertEquals(True, alert._alertSent(1))
        self.assertEquals(False, alert._alertSent(0))


from django.core import mail
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from allauth.account.models import EmailAddress

# Create your tests here.
from eggplant.factories import UserFactory, DepartmentFactory, \
    AccountFactory
from eggplant.profiles.models import UserProfile


class TestProfile(TestCase):

    def setUp(self):
        self.user = UserFactory()
        self.user.set_password('pass')
        self.user.save()
        email_address = EmailAddress.objects\
            .add_email(None, self.user, 'test@food.net', confirm=False,
                       signup=False)
        email_address.verified = True
        email_address.primary = True
        email_address.save()

    def test_profile(self):
        response = self.client.get(reverse('eggplant:profiles:profile'))
        url = reverse('account_login') + '?next=' + \
            reverse('eggplant:profiles:profile')
        self.assertRedirects(response, url, status_code=302,
                             target_status_code=200, msg_prefix='')

        self.client.login(username='test@food.net', password='pass')
        response = self.client.get(reverse('eggplant:profiles:profile'))
        expected = 'form method="post" enctype="multipart/form-data" action="%s"' % reverse('eggplant:profiles:profile')
        self.assertContains(response, expected, 1, 200)

        data = {
            'first_name': 'Joe',
            'middle_name': 'Frank',
            'last_name': 'Doe',
            'address': '123 Sunset av. NY, USA',
            'postcode': '123321ABCD',
            'city': 'New York',
            'tel': '79231232',
            'sex': UserProfile.FEMALE,
        }
        response = self.client.post(reverse('eggplant:profiles:profile'),
                                    data=data)
        self.assertRedirects(response, reverse('eggplant:dashboard:home'),
                             status_code=302,
                             target_status_code=200, msg_prefix='')

        expected = {
            'middle_name': 'Frank',
            'address': '123 Sunset av. NY, USA',
            'postcode': '123321ABCD',
            'sex': UserProfile.FEMALE,
            'city': 'New York',
            'tel': '79231232',
        }
        profile = UserProfile.objects.get(user_id=self.user.id)
        self.assertDictContainsSubset(expected, profile.__dict__)
        user = User.objects.get(id=self.user.id)
        self.assertEqual(user.first_name, 'Joe')
        self.assertEqual(user.last_name, 'Doe')

    def test_user_profile(self):
        self.assertIsNotNone(self.user.profile)

    def test_user_member_department_models(self):
        # Although this may look like testing ORM API I thought it
        # would be good to just write a test to show how we expect
        # membership to work
        department = DepartmentFactory()
        user2 = UserFactory()
        user2.profile.save()
        account = AccountFactory(department=department)
        account.user_profiles.add(user2.profile)
        account.user_profiles.add(self.user.profile)
        self.assertEqual(2, account.user_profiles.all().count())

        # we don't have to have a fresh copy of dept
        self.assertEqual(1, department.accounts.count())
        department.accounts.all().delete()
        self.assertEqual(0, department.accounts.count())


class TestSignup(TestCase):

    def test_signup_get(self):
        url = reverse('eggplant:profiles:signup')
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'eggplant/profiles/signup.html')

    def test_signup_post(self):
        url = reverse('eggplant:profiles:signup')
        profile_data = {
            'address': 'Vestergade 20c',
            'city': 'København',
            'postcode': '1456',
            'tel': '+45 71 99 91 93',
            'sex': 'other',
        }
        user_data = {
            'first_name': 'test first name',
            'last_name': 'test last name',
            'email': 'test@localhost',
            'password1': '!super secure123',
            'password2': '!super secure123',
        }
        user_data.update(profile_data)
        response = self.client.post(url, user_data, follow=True)
        expected_url = reverse('account_email_verification_sent')
        self.assertRedirects(response, expected_url, status_code=302,
                             target_status_code=200, msg_prefix='')
        user_query = User.objects.filter(email=user_data['email'])
        self.assertEqual(1, user_query.count())

        actual = user_query[0]
        profile_query = UserProfile.objects.filter(user=actual, **profile_data)
        self.assertEqual(1, profile_query.count())

        address_query = EmailAddress.objects.filter(email=user_data['email'])
        self.assertEqual(1, address_query.count())

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject,
                         '[localhost] Confirm e-mail address')

# MailToolsBox

MailToolsBox is a Python library for dealing with Email handling in easy way.

## Installation

Use the package manager [pip](https://ramai.io) to install MailToolsBox.

```bash
pip install MailToolsBox
```

## Usage

```python
import MailToolsBox.mailSender
mail = MailToolsBox.mailSender.SendAgent(user_email='username@gmail.com', server_smtp_address='smtp.gmail.com', user_email_password='User Password', port=587)
mail.send_mail(recipent_email='user@gmail.com', subject='This is Subject Text', message_Body='This is  Body Text')
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)


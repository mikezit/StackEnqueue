import os.path
from base import Setting, SettingSet
from django.utils.translation import ugettext_lazy as _

UPLOAD_SET = SettingSet('paths', _('File upload settings'), _("File uploads related settings."), 600)

UPFILES_FOLDER = Setting('UPFILES_FOLDER', os.path.join(os.path.dirname(os.path.dirname(__file__)),'upfiles'), UPLOAD_SET, dict(
label = _("Uploaded files folder"),
help_text = _("The filesystem path where uploaded files will be stored. Please note that this folder must exist.")))

UPFILES_ALIAS = Setting('UPFILES_ALIAS', '/upfiles/', UPLOAD_SET, dict(
label = _("Uploaded files alias"),
help_text = _("The url alias for uploaded files. Notice that if you change this setting, you'll need to restart your site.")))

GRAVATAR_FOLDER = Setting('GRAVATAR_FOLDER', os.path.join(os.path.dirname(os.path.dirname(__file__)),'gravatar'), UPLOAD_SET, dict(
label = _("Uploaded gravatar folder"),
help_text = _("The filesystem path where uploaded files will be stored. Please note that this folder must exist.")))

GRAVATAR_ALIAS = Setting('GRAVATAR_ALIAS', '/gravatar/', UPLOAD_SET, dict(
label = _("Uploaded gravatar alias"),
help_text = _("The url alias for uploaded files. Notice that if you change this setting, you'll need to restart your site.")))

FLAIR_FOLDER = Setting('FLAIR_FOLDER', os.path.join(os.path.dirname(os.path.dirname(__file__)),'flair'), UPLOAD_SET, dict(
label = _("generated flair folder"),
help_text = _("The filesystem path where the user flair will be stored. Please note that this folder must exist.")))

ALLOW_MAX_FILE_SIZE = Setting('ALLOW_MAX_FILE_SIZE', 2.5, UPLOAD_SET, dict(
label = _("Max file size"),
help_text = _("The maximum allowed file size for uploads in mb.")))

GRAVATAR_MAX_WIDTH  = Setting('GRAVATAR_MAX_WIDTH', 1680, UPLOAD_SET, dict(
label = _("Max gravatar width"),
help_text = _("The maximum allowed gravatar width for uploads in mb.")))

GRAVATAR_MAX_HEIGHT = Setting('GRAVATAR_MAX_HEIGHT', 1024, UPLOAD_SET, dict(
label = _("Max gravatar height"),
help_text = _("The maximum allowed gravatar height for uploads in mb.")))



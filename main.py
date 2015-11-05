import webapp2
import cgi
import re
import os
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
								autoescape = True)
								
import hashlib
import hmac

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASSWORD_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

class User(db.Model):
	username = db.StringProperty(required = True)
	encrypted_password = db.StringProperty(required = True)
	email = db.StringProperty(required = False)
	

def escape_html(s):
    return cgi.escape(s, quote = True)

def rot13(str):
	list = []
	
	for c in str:
		if c.isalpha():
			if c.islower():
				temp = (ord(c)-97 +13) % 26 + 97
				list.append(chr(temp))
			else:
				temp = (ord(c)-65 +13) % 26 + 65
				list.append(chr(temp))
		else:
			list.append(c)
			
	return ''.join(list)
	
def validate_username(username):
	return USER_RE.match(username)

	
def isDuplicate_username(input_username):
	users = db.GqlQuery("SELECT * FROM User")
	for user in users:
		if user.username == input_username:
			return True
	return False

def validate_password(password):
	return PASSWORD_RE.match(password)

def validate_email(email):
	return EMAIL_RE.match(email)


rot13form = """
<!DOCTYPE html>

<html>
  <head>
    <title>Unit 2 Rot 13</title>
  </head>

  <body>
    <h2>Enter some text to ROT13:</h2>
    <form method="post">
      <textarea name="text"
                style="height: 100px; width: 400px;">%s</textarea>
      <br>
      <input type="submit">
    </form>
  </body>

</html>
"""

form = """
<!DOCTYPE html>

<html>
  <head>
    <title>Unit 2 Rot 13</title>
    <style type="text/css">
      .label {text-align: right}
      .error {color: red}
    </style>

  </head>

  <body>
    <h2>Signup</h2>
    <form method="post">
      <table>
        <tr>
          <td class="label">
            Username
          </td>
          <td>
            <input type="text" name="username" value="%(username)s">
          </td>
          <td class="error">
            %(error_username)s
          </td>
        </tr>

        <tr>
          <td class="label">
            Password
          </td>
          <td>
            <input type="password" name="password" value="">
          </td>
          <td class="error">
            %(error_password)s
          </td>
        </tr>

        <tr>
          <td class="label">
            Verify Password
          </td>
          <td>
            <input type="password" name="verify" value="">
          </td>
          <td class="error">
            %(error_verify)s
          </td>
        </tr>

        <tr>
          <td class="label">
            Email (optional)
          </td>
          <td>
            <input type="text" name="email" value="%(email)s">
          </td>
          <td class="error">
            %(error_email)s
          </td>
        </tr>
      </table>

      <input type="submit">
    </form>
  </body>

</html>
"""


SECRET = 'imsosecret'
def hash_str(s):
    return hmac.new(SECRET, s).hexdigest()

def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))

def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val
	
	
def encryptPassword(str):
	#Implement encryption logic
	return str
	
class SignupPage(webapp2.RequestHandler):
    def write_form(self, username="", error_username="", error_password="", error_verify="", email="", error_email=""):
		self.response.out.write(form % {"username": username,
								"error_username": error_username,
								"error_password": error_password,
								"error_verify": error_verify,
								"email": email,
								"error_email": error_email})

    def get(self):
        self.write_form()
		#self.response.out.write(form)
		
    def post(self):
		input_username = self.request.get("username")
		input_password = self.request.get("password")
		input_verify = self.request.get("verify")
		input_email = self.request.get("email")
		error = False
		error_username = ""
		error_email = ""
		error_password = ""
		error_verify = ""
		
		if not validate_username(input_username):
			error_username = "Invalid Username"
			error = True
		if isDuplicate_username(input_username):
			error_username = "The username already exists"
			error = True
		if not validate_password(input_password):
			error_password = "Invalid Password"
			error = True
		if (input_password != input_verify):
			error_verify = "Password Doesn't Match"
			error = True
		if input_email != "":
			if not validate_email(input_email):
				error_email = "Invalid Email"
				error = True
		
		
		if error:
			self.write_form(input_username, error_username, error_password, error_verify, input_email, error_email)
		else: #If no error
			a = User(username = input_username, encrypted_password = encryptPassword(input_password), email = input_email)
			a.put()
			#self.response.headers.add_header('Set-Cookie', 'name=value; Path=/')'
			cookie = make_secure_val(input_username)
			self.response.headers.add_header('Set-Cookie', 'user_id=%s' % str(cookie))
			self.redirect('/welcome')

class Welcome(webapp2.RequestHandler):
	def get(self):
		user_id_cookie = self.request.cookies.get("user_id")
		if user_id_cookie:
			username = check_secure_val(user_id_cookie)
			if username:
				self.response.out.write("Welcome, " + str(username))
			else:
				self.redirect('/signup')

class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)
		
	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))
		
class Shopping(Handler):
	def get(self):
		items = self.request.get_all("food")
		self.render("shopping_list.html", items = items)
		
class Art(db.Model):
	title = db.StringProperty(required = True)
	art = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	
		
class AsciiChan(Handler):
	def render_front(self, title="", art="", error=""):
		arts = db.GqlQuery("SELECT * FROM Art "
							"ORDER BY created DESC ")
		
		self.render("front.html", title=title, art=art, error=error, arts=arts)
		
	def get(self):
		self.render_front()
		
	def post(self):
		title = self.request.get("title")
		art = self.request.get("art")
		
		if title and art:
			a = Art(title = title, art = art)
			a.put()
			
			self.redirect("/asciichan")
			
		else:
			error = "we need both a title and some artwork!"
			self.render_front(title, art, error)

class Entry(db.Model):
	title = db.StringProperty(required = True)
	entry = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
			
class Blog(Handler):
	def get(self):
		entries = db.GqlQuery("SELECT * FROM Entry "
							"ORDER BY created DESC limit 10")
		self.render("front.html", entries=entries)
		
class NewPost(Handler):
	def render_blog(self, title="", entry="", error=""):
		self.render("new-post.html", title=title, entry=entry, error=error)

	def get(self):
		self.render_blog()
		
	def post(self):
		title = self.request.get("subject")
		entry = self.request.get("content")
		
		if title and entry:
			a = Entry(title = title, entry = entry)
			a.put()
			entry_id = a.key().id()
			self.redirect("/blog/" + str(entry_id))
			
		else:
			error = "we need both a title and an entry!"
			self.render_blog(title, entry, error)

class ReviewPost(Handler):
	def get(self, entryid):
		entry_obj = Entry.get_by_id(long(entryid))
		if not entry_obj:
			self.error(404)
			return
		title = entry_obj.title
		entry = entry_obj.entry
		self.render("entry.html", title=title, entry=entry)
			
app = webapp2.WSGIApplication([('/signup', SignupPage),
                              ('/welcome', Welcome),
							  ('/shopping', Shopping),
							  ('/asciichan', AsciiChan),
							  ('/blog', Blog),
							  ('/blog/newpost', NewPost),
							  (r'/blog/(\d+)', ReviewPost)],
                             debug=True)
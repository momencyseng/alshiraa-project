from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, FileField, TextAreaField, FloatField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class ProductForm(FlaskForm):
    name = StringField('اسم المنتج', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('وصف المنتج', validators=[DataRequired()])
    category = SelectField('الفئة', choices=[
        ('solar', 'طاقة شمسية (Solar Energy)'),
        ('security', 'كاميرات أمنية (Security Cameras)'),
        ('inverter', 'شواحن عاكسات وألواح (Chargers & Inverters)')
    ], validators=[DataRequired()])
    price = FloatField('السعر (بالدينار)', default=0.0)
    stock = IntegerField('الكمية المتوفرة', default=0)
    is_special_offer = BooleanField('عرض خاص؟')
    image = FileField('صورة المنتج')
    submit = SubmitField('إضافة / حفظ')

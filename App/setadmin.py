from app import db, User

username = input('Username >> ')

user = User.query.filter_by(username=username).first()      

user.admin = True

db.session.commit()

print(f'{username} is now admin')
from passlib.context import CryptContext
from db import load_df, execute

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    password = password[:72]  #  bcrypt limit fix
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    password = password[:72]
    return pwd_context.verify(password, hashed)

def create_user(username: str, password: str):
    hashed = hash_password(password)

    execute(
        "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
        (username, hashed)
    )
    print("PASSWORD RECEIVED:", password)
    print("LENGTH:", len(password))


def authenticate_user(username: str, password: str):
    df = load_df(
        "SELECT * FROM users WHERE username = %s",
        (username,)
    )

    if df.empty:
        return None

    user = df.iloc[0]

    if verify_password(password, user["password_hash"]):
        return dict(user)

    return None
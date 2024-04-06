
FROM python:3.12.2-slim

RUN pip install pipenv

WORKDIR /usr/src/app

COPY Pipfile Pipfile.lock ./

RUN pipenv install --deploy --ignore-pipfile

COPY . .

EXPOSE 3000

CMD ["pipenv", "run", "python", "main.py"]

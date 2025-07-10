def my_decorator(func):
    def wrapper():
        print("Что-то происходит до вызова функции.")
        result = func()
        print("Что-то происходит после вызова функции.")
        return result

    return wrapper


@my_decorator
def say_hello():
    print("Привет!")


say_hello()

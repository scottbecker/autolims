def str_respresents_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False  
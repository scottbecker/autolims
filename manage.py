#!/usr/bin/env python
import os
import sys



if __name__ == "__main__":
    
    sys.path.append("./autolims")
    
    print sys.path
    print os.path.dirname(os.path.realpath(__file__))
    
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    for f in files:    
        print f    
    from lib import round_up    

    
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    execute_from_command_line(sys.argv)

"""Simple Event Manager Based on Pipes
"""

from medusa.select_trigger import trigger

Wakeup=trigger().pull_trigger

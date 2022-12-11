import logging

from src.filter.operator import Operator

logger = logging.getLogger(__name__)


class RuleCollection:
    def __init__(self, match_all=True, active=True):
        self.rules = []
        self.match_all = match_all
        self.active = active

    # define a __dict__ magic method that returns the data to be serialized to JSON
    def __dict__(self):
        return {
            'rules': self.rules,
            'match_all': self.match_all,
            'active': self.active,
        }

    def add(self, element, operator, value, negate=False, active=True):
        self.rules.append((element, operator, value, negate, active))

    def remove(self, element, operator, value, negate=False, active=True):
        self.rules.remove((element, operator, value, negate, active))

    def check(self, source) -> bool:
        if not self.active:
            return True

        result = True
        for element, operator, value, negate, active in self.rules:
            if not active:
                continue
            result = False

            something = source.get(element, "")
            is_satisfied = Operator.get_function(operator)(something, value)

            if negate:
                is_satisfied = not is_satisfied

            if self.match_all:
                if not is_satisfied:
                    return False
            else:
                if is_satisfied:
                    return True

        if self.match_all:
            return True
        return result


class RuleManager:
    def __init__(self):
        self.collections = {}

    def __dict__(self):
        return {
            'Rules': {
                name: collection.__dict__()
                for name, collection in self.collections.items()
            }
        }

    def add_collection(self, name, collection):
        self.collections[name] = collection

    def remove_collection(self, name):
        try:
            self.collections.pop(name)
        except KeyError:
            logger.info(f"Failed to remove collection {name}")

    def check(self, source):
        for collection in self.collections.values():
            if not collection.active:
                continue

            if not collection.check(source):
                return False

        return True

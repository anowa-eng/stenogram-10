from typing import Generic, List, Mapping, Sequence, Type, TypeVar

_registry: Mapping[str, list] = {}

def _register_inst(instance) -> None:
    class_name = instance.__class__.__name__

    if not _registry.get(class_name):
        _registry[class_name] = []
    
    _registry[class_name].append(instance)

    instance.id = len(_registry[class_name]) - 1

def _get_registry(class_name: str) -> List:
    if not _registry.get(class_name):
        _registry[class_name] = []
    
    return _registry[class_name]

def indexed(func):
    def wrapper(self, *args, **kwargs):
        _register_inst(self)
        self.__class__.registry = _registry[self.__class__.__name__]
        func(self, *args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------- #

T = TypeVar('T', bound='IndexedClass')

class IndexedClass(Generic[T]):
    id: int
    registry: List[T]

    def __init_subclass__(self):
        self.registry = self._registry()
        self.registry.append(self)

    @classmethod
    def _registry(cls: Type[T]) -> List[T]:
        # Get the registry associated with the class from the _registry dictionary.
        # If the registry does not exist, create an empty list and add it to the dictionary.
        # Finally, return the registry.
        return _get_registry(cls.__name__)

    # ---------------------------------------------------------------------------- #

    @classmethod
    def id(cls: Type[T], id: int) -> T:
        return cls.registry[id]
    
    @classmethod
    def ids(cls: Type[T], ids: Sequence[int]) -> List[T]:
        return tuple(cls.registry[id] for id in ids)
    
    @classmethod
    def reset_all_id(cls: Type[T]) -> None:
        cls.registry.clear()


from maxapi.context import State, StatesGroup


class FSMstates(StatesGroup):
    is_writing_task = State()
    is_choosing_goal = State()
    is_choosing_time = State()
    is_choosing_tree = State()
    is_free = State()
    is_changing_goal = State()
    is_asking_for_periodic = State()
    is_setting_custom_time = State()

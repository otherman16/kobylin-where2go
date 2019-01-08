import redis
import os


class DB:
    """ DataBse object """

    REDIS_URL = os.environ.get('REDIS_URL')
    db = redis.Redis.from_url(REDIS_URL)
    # db.flushdb()


class User:
    """ User object class """

    STATE_IDLE = 0

    STATE_ADD_START, STATE_ADD_NAME, STATE_ADD_LOCATION, STATE_ADD_PHOTO, STATE_ADD_SAVE = \
        1, 2, 3, 4, 5

    STATE_RESET_START, STATE_RESET_DO = \
        6, 7

    def __init__(self, user_id=0, name=''):
        self.id = user_id
        self.name = name
        self.count = 0
        self.state = self.STATE_IDLE
        self.new_place = InterestPlace()

    @staticmethod
    def key(user_id):
        return f"user:{user_id}"

    @classmethod
    def exists(cls, user_id):
        return DB.db.exists(cls.key(user_id)) == 1

    @classmethod
    def get(cls, user_id):
        user = None
        user_key = cls.key(user_id)
        if DB.db.exists(user_key):
            queryset = DB.db.hgetall(user_key)
            user = cls()
            user.id = user_id
            user.name = queryset[b'name'].decode()
            user.count = int(queryset[b'count'].decode())
            user.state = int(queryset[b'state'].decode())
            user.new_place.name = queryset[b'new_place.name'].decode()
            user.new_place.location = (float(queryset[b'new_place.location.latitude'].decode()),
                                       float(queryset[b'new_place.location.longitude'].decode()))
            user.new_place.address = queryset[b'new_place.address'].decode()
            user.new_place.photo = queryset[b'new_place.photo']
        return user

    def save(self):
        DB.db.hmset(self.key(self.id), {
            'name': self.name,
            'count': self.count,
            'state': self.state,
            'new_place.name': self.new_place.name,
            'new_place.location.latitude': self.new_place.location[0],
            'new_place.location.longitude': self.new_place.location[1],
            'new_place.address': self.new_place.address,
            'new_place.photo': self.new_place.photo
        })

    def save_new_place(self):
        self.count += 1
        self.new_place.id = self.count
        self.new_place.save(self)
        self.save()

    def delete(self):
        return DB.db.delete(self.key(self.id)) == 1

    @classmethod
    def create(cls, user_id, name):
        user = cls()
        user.id = user_id
        user.name = name
        user.count = 0
        user.state = User.STATE_IDLE
        user.new_place = InterestPlace()
        user.save()
        return user

    def __str__(self):
        return f"User[id: {self.id}, name: {self.name}, count: {self.count}, state: {self.state}, " \
            f"new_place: {self.new_place}]"


class InterestPlace:
    """ Interest Place object class """

    def __init__(self):
        self.id = 0
        self.name = ''
        self.location = (0.0, 0.0)
        self.address = ''
        self.photo = b''

    @staticmethod
    def key(user_id, interest_place_id):
        return f"{User.key(user_id)}:interest_place:{interest_place_id}"

    @classmethod
    def exists(cls, user_id, interest_place_id):
        return DB.db.exists(cls.key(user_id, interest_place_id)) == 1

    @classmethod
    def get(cls, user_id, interest_place_id):
        interest_place = None
        interest_place_key = cls.key(user_id, interest_place_id)
        if DB.db.exists(interest_place_key):
            queryset = DB.db.hgetall(interest_place_key)
            interest_place = cls()
            interest_place.id = interest_place_id
            interest_place.name = queryset[b'name'].decode()
            interest_place.location = (float(queryset[b'location.latitude'].decode()),
                                       float(queryset[b'location.longitude'].decode()))
            interest_place.address = queryset[b'address'].decode()
            interest_place.photo = queryset[b'photo']
        return interest_place

    def save(self, user: User):
        DB.db.hmset(self.key(user.id, self.id), {
            'name': self.name,
            'location.latitude': self.location[0],
            'location.longitude': self.location[1],
            'address': self.address,
            'photo': self.photo
        })

    def delete(self, user: User):
        return DB.db.delete(self.key(user.id, self.id)) == 1

    @classmethod
    def create(cls, user: User, name, location, address, photo):
        user.count += 1
        interest_place = cls()
        interest_place.id = user.count
        interest_place.name = name
        interest_place.location = location or (0.0, 0.0)
        interest_place.address = address or ''
        interest_place.photo = photo or b''
        interest_place.save(user)
        return interest_place

    @staticmethod
    def all(user: User):
        interest_places = []
        for interest_place_id in range(1, user.count + 1):
            interest_place = InterestPlace.get(user.id, interest_place_id)
            if interest_place:
                interest_places.append(interest_place)
        return interest_places

    @staticmethod
    def reset(user: User):
        for interest_place_id in range(1, user.count + 1):
            interest_place = InterestPlace.get(user.id, interest_place_id)
            if interest_place:
                interest_place.delete(user)
        user.count = 0
        user.save()

    def __str__(self):
        return f"InterestPlace[id: {self.id}, name: {self.name}, location: {self.location}, address: {self.address}]"

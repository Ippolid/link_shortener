package database

type Value struct {
	UserId       int64
	OriginalLink string
	ShortLink    string
	ExpireTime   int64
}
type Storage struct {
	Inner []Value
}

func NewStorage() (Storage, error) {
	return Storage{
		Inner: make([]Value, 0, 100),
	}, nil
}

func (r *Storage) AppendElem(userid int64, originallink string, shortlink string, expire int64) {
	r.Inner = append(r.Inner, Value{UserId: userid, OriginalLink: originallink, ShortLink: shortlink, ExpireTime: expire})
}

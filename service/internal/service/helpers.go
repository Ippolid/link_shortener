package service

import (
	"crypto/sha1"
	"encoding/hex"
)

const domen string = "http://loclahost:8090/"

func GenerateShortURL(url string) string {
	hash := sha1.New()
	hash.Write([]byte(url))
	return hex.EncodeToString(hash.Sum(nil))[:8]
}

func NewLink(oldlink string) string {
	indeficator := GenerateShortURL(oldlink)
	return domen + indeficator
}

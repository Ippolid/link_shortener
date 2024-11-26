package service

import (
	"crypto/sha1"
	"encoding/hex"
)

func GenerateShortURL(url string) string {
	hash := sha1.New()
	hash.Write([]byte(url))
	return hex.EncodeToString(hash.Sum(nil))[:8]
}

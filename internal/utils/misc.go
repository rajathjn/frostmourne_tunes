package utils

import (
	"github.com/joho/godotenv"
)

func LoadEnvFile(path string) error {
	err := godotenv.Load(path)
	return err
}

package main

import (
	"fmt"
	"ecc608"
)

func main() {
	serial := ecc608.Serial()
	fmt.Println(serial)

	keyPem := ecc608.PublicKey(0)
	fmt.Println(keyPem)

	fmt.Println(ecc608.GetCloudIoTJWT("test-project-id", 60))
}
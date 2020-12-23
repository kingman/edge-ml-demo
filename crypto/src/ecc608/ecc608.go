package ecc608

/*
#include <stdlib.h>
#include "c_lib/custom_cryptoauthlib.h"
ATCA_STATUS init() {
        ATCAIfaceCfg* gCfg = &cfg_ateccx08a_i2c_default;
		gCfg->atcai2c.bus = 0;
		gCfg->devtype = 3;
        return atcab_init(gCfg);
}
*/
import "C"
import (
        "fmt"
        "unsafe"
        "encoding/hex"
        "encoding/base64"
		"strings"
		"time"
)

var InitStatus C.ATCA_STATUS

func init() {
	InitStatus = C.init()	
}


func PublicKey(keyId C.ushort) string {
	if InitStatus == 0 {
		var publicKey [64]uint8
		status := C.atcab_get_pubkey(keyId, (*C.uchar)(unsafe.Pointer(&publicKey)))
		if status == 0 {
			return convertECPubToPem(publicKey[:])
		}
	}
	return "Unable to reach the secure element"
}

func Serial() string {
	if InitStatus == 0 {
		var serial [9]uint8
		status := C.atcab_read_serial_number((*C.uchar)(unsafe.Pointer(&serial)))
		if status == 0 {
			return asciiHexString(serial[:])
		}
	}
	return "Unable to reach the secure element"
}

func GetCloudIoTJWT(projectId string, validSec int) string {
	var jwt C.atca_jwt_t
	buf := C.malloc(C.sizeof_char * 512)
	defer C.free(unsafe.Pointer(buf))

	status := C.atca_jwt_init(&jwt, (*C.char)(buf), 512)

	if status != 0 {
		return "Initialize JWT failed"
	}

	aud := C.CString("aud")
	defer C.free(unsafe.Pointer(aud))
	audVal := C.CString(projectId)
	defer C.free(unsafe.Pointer(audVal))

	status = C.atca_jwt_add_claim_string(&jwt, aud, audVal)
	if status != 0 {
		return "Add 'aud' claim failed"
	}

	iat := C.CString("iat")
	defer C.free(unsafe.Pointer(iat))
	iatVal := C.int32_t(time.Now().Unix())

	status = C.atca_jwt_add_claim_numeric(&jwt, iat, iatVal)
	if status != 0 {
		return "Add 'iat' claim failed"
	}

	exp := C.CString("exp")
	defer C.free(unsafe.Pointer(exp))
	expVal := C.int32_t(time.Now().Add(time.Duration(validSec) * time.Second).Unix())

	status = C.atca_jwt_add_claim_numeric(&jwt, exp, expVal)
	if status != 0 {
		return "Add 'exp' claim failed"
	}

	status = C.atca_jwt_finalize(&jwt, 0)
	if status != 0 {
		return "Finalize JWT failed"
	}
	
	b := C.GoBytes(buf, (C.int)(jwt.cur))

	return string(b)
}

func asciiHexString(data []byte) string {
	return splitArrayToEqualParts(data,16)
}

func convertECPubToPem(rawKey []byte) string {
        keyPrefix, _ := hex.DecodeString("3059301306072A8648CE3D020106082A8648CE3D03010703420004")
        publicKeyDer := append(keyPrefix, rawKey...)
        publicKeyStr := base64.StdEncoding.EncodeToString(publicKeyDer)
        return fmt.Sprintf("-----BEGIN PUBLIC KEY-----\n%s\n-----END PUBLIC KEY-----", splitToEqualParts(publicKeyStr, 64))
}

func splitArrayToEqualParts(input []byte,length int) string {
	slen := len(input)
	var sArray []string
	j := 0
	for i := 0; i < slen; i+=length {
			j = i+length
			if j > slen {
					j = slen
			}
			sArray = append(sArray, strings.ToUpper(hex.Dump(input[i:j])))
	}
	return strings.Join(sArray, "\n")
}

func splitToEqualParts(input string,length int) string {
        slen := len(input)
        var sArray []string
        j := 0
        for i := 0; i < slen; i+=length {
                j = i+length
                if j > slen {
                        j = slen
                }
                sArray = append(sArray, input[i:j])
        }
        return strings.Join(sArray, "\n")
}
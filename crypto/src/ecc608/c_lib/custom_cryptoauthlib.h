#include "atca_status.h"
#include "atca_iface.h"
#include "atca_cfgs.h"

ATCA_STATUS atcab_init(ATCAIfaceCfg *cfg);
ATCA_STATUS atcab_get_pubkey(uint16_t key_id, uint8_t* public_key);
ATCA_STATUS atcab_read_serial_number(uint8_t* serial_number);
ATCA_STATUS atcab_sign(uint16_t key_id, const uint8_t* msg, uint8_t* signature);
ATCA_STATUS atcab_sha(uint16_t length, const uint8_t* message, uint8_t* digest);

typedef struct
{
    char*    buf;          /* Input buffer */
    uint16_t buflen;       /* Total buffer size */
    uint16_t cur;          /* Current location in the buffer */
} atca_jwt_t;

ATCA_STATUS atca_jwt_init(atca_jwt_t* jwt, char* buf, uint16_t buflen);
ATCA_STATUS atca_jwt_add_claim_string(atca_jwt_t* jwt, const char* claim, const char* value);
ATCA_STATUS atca_jwt_add_claim_numeric(atca_jwt_t* jwt, const char* claim, int32_t value);
ATCA_STATUS atca_jwt_finalize(atca_jwt_t* jwt, uint16_t key_id);
void atca_jwt_check_payload_start(atca_jwt_t* jwt);
ATCA_STATUS atca_jwt_verify(const char* buf, uint16_t buflen, const uint8_t* pubkey);

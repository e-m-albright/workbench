// Regression for GHSA-86w9-cpqp-85rv, plus valid PKCS#1 v1.5 and PSS signatures.
const assert = require("node:assert/strict");
const { generateKeyPairSync } = require("node:crypto");
const { createRequire } = require("node:module");
const path = require("node:path");
const forge = createRequire(path.resolve(process.argv[2], "package.json"))("node-forge");
const { privateKey: pem } = generateKeyPairSync("rsa", {
  modulusLength: 1024,
  privateKeyEncoding: { type: "pkcs1", format: "pem" },
  publicKeyEncoding: { type: "spki", format: "pem" },
});
const key = forge.pki.privateKeyFromPem(pem);
const pub = forge.pki.setRsaPublicKey(key.n, key.e);
const md = forge.md.sha256.create().update("workbench synthetic signature probe");
const digest = md.digest().getBytes();
const asn1 = forge.asn1;
const item = (type, constructed, value) => asn1.create(asn1.Class.UNIVERSAL, type, constructed, value);

for (const parameters of [false, true]) {
  for (const garbage of [false, true]) {
    const algorithm = [item(asn1.Type.OID, false, asn1.oidToDer(forge.oids.sha256).getBytes())];
    if (parameters) algorithm.push(item(asn1.Type.NULL, false, ""));
    if (garbage) algorithm.push(item(asn1.Type.OCTETSTRING, false, "unconsumed bytes"));
    const info = item(asn1.Type.SEQUENCE, true, [
      item(asn1.Type.SEQUENCE, true, algorithm),
      item(asn1.Type.OCTETSTRING, false, digest),
    ]);
    const signature = key.sign(asn1.toDer(info).getBytes(), "NONE");
    if (garbage && !process.argv.includes("--unpatched")) {
      assert.throws(() => pub.verify(digest, signature), /DigestInfo/);
    } else {
      assert.equal(pub.verify(digest, signature), true);
    }
  }
}
const valid = key.sign(md);
assert.equal(pub.verify(digest, valid), true);
assert.equal(pub.verify("x".repeat(32), valid), false);
const pss = forge.pss.create({
  md: forge.md.sha256.create(),
  mgf: forge.mgf.mgf1.create(forge.md.sha256.create()),
  saltLength: 20,
});
assert.equal(pub.verify(digest, key.sign(md, pss), pss), true);
console.log(process.argv.includes("--unpatched")
  ? "Confirmed original nested-DigestAlgorithm defect"
  : "Verified repaired RSA validation and valid signatures");

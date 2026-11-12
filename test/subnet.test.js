/**
 * SQA Test Suite for Subnet Calculator
 * Mencakup Equivalence Partitioning (EP) dan Boundary Value Analysis (BVA)
 */

const SubnetCalculator = require('../js/calculator.js');

let passedTests = 0;
let failedTests = 0;
const results = [];

function assert(description, condition, actual, expected) {
  if (condition) {
    passedTests++;
    results.push({ status: 'PASS', description });
    console.log(`\x1b[32m✔ PASS:\x1b[0m ${description}`);
  } else {
    failedTests++;
    results.push({ status: 'FAIL', description, actual, expected });
    console.error(`\x1b[31m✖ FAIL:\x1b[0m ${description}`);
    console.error(`  Expected: ${JSON.stringify(expected)}`);
    console.error(`  Actual:   ${JSON.stringify(actual)}`);
  }
}

console.log('========================================================');
console.log('   MENJALANKAN AUTOMATED TEST SUITE: SUBNET CALCULATOR  ');
console.log('========================================================\n');

// --- 1. EQUIVALENCE PARTITIONING: KELAS C STANDAR (/24) ---
console.log('[Kategori 1: Subnetting Standar Class C /24]');
{
  const res = SubnetCalculator.calculateSubnet('192.168.1.15', 24);
  assert('Kalkulasi berhasil tanpa error', res.success === true, res.success, true);
  assert('Network Address tepat', res.results.networkAddress === '192.168.1.0', res.results.networkAddress, '192.168.1.0');
  assert('Broadcast Address tepat', res.results.broadcastAddress === '192.168.1.255', res.results.broadcastAddress, '192.168.1.255');
  assert('Rentang host pertama tepat', res.results.firstUsableHost === '192.168.1.1', res.results.firstUsableHost, '192.168.1.1');
  assert('Rentang host terakhir tepat', res.results.lastUsableHost === '192.168.1.254', res.results.lastUsableHost, '192.168.1.254');
  assert('Jumlah host usable tepat (254)', res.results.usableHosts === 254, res.results.usableHosts, 254);
  assert('Total host tepat (256)', res.results.totalHosts === 256, res.results.totalHosts, 256);
  assert('Subnet Mask tepat', res.results.subnetMask === '255.255.255.0', res.results.subnetMask, '255.255.255.0');
  assert('Wildcard Mask tepat', res.results.wildcardMask === '0.0.0.255', res.results.wildcardMask, '0.0.0.255');
  assert('Kelas IP tepat (Kelas C)', res.results.ipClass === 'Kelas C', res.results.ipClass, 'Kelas C');
  assert('Tipe Private tepat', res.results.isPrivate === true, res.results.isPrivate, true);
}

// --- 2. EQUIVALENCE PARTITIONING: KELAS B STANDAR (/16) & KELAS A (/8) ---
console.log('\n[Kategori 2: Subnetting Standar Class B /16 & Class A /8]');
{
  const resB = SubnetCalculator.calculateSubnet('172.16.50.88', 16);
  assert('Class B Network Address tepat', resB.results.networkAddress === '172.16.0.0', resB.results.networkAddress, '172.16.0.0');
  assert('Class B Broadcast Address tepat', resB.results.broadcastAddress === '172.16.255.255', resB.results.broadcastAddress, '172.16.255.255');
  assert('Class B Usable Hosts tepat (65534)', resB.results.usableHosts === 65534, resB.results.usableHosts, 65534);

  const resA = SubnetCalculator.calculateSubnet('10.20.30.40', 8);
  assert('Class A Network Address tepat', resA.results.networkAddress === '10.0.0.0', resA.results.networkAddress, '10.0.0.0');
  assert('Class A Broadcast Address tepat', resA.results.broadcastAddress === '10.255.255.255', resA.results.broadcastAddress, '10.255.255.255');
  assert('Class A Usable Hosts tepat (16777214)', resA.results.usableHosts === 16777214, resA.results.usableHosts, 16777214);
}

// --- 3. BOUNDARY VALUE ANALYSIS (BVA): PREFIX BATAS KANAN (/30, /31, /32) ---
console.log('\n[Kategori 3: Boundary Value Analysis - Prefix Tinggi /30, /31, /32]');
{
  // /30: Subnet 4 IP, 2 usable host
  const res30 = SubnetCalculator.calculateSubnet('192.168.1.13', 30);
  assert('/30 Network Address tepat', res30.results.networkAddress === '192.168.1.12', res30.results.networkAddress, '192.168.1.12');
  assert('/30 Broadcast Address tepat', res30.results.broadcastAddress === '192.168.1.15', res30.results.broadcastAddress, '192.168.1.15');
  assert('/30 Usable Hosts tepat (2)', res30.results.usableHosts === 2, res30.results.usableHosts, 2);

  // /31: RFC 3021 Point-to-Point
  const res31 = SubnetCalculator.calculateSubnet('10.0.0.2', 31);
  assert('/31 Network Address tepat', res31.results.networkAddress === '10.0.0.2', res31.results.networkAddress, '10.0.0.2');
  assert('/31 Broadcast Address tepat', res31.results.broadcastAddress === '10.0.0.3', res31.results.broadcastAddress, '10.0.0.3');
  assert('/31 Usable Hosts tepat (2 RFC 3021)', res31.results.usableHosts === 2, res31.results.usableHosts, 2);

  // /32: Host Route
  const res32 = SubnetCalculator.calculateSubnet('192.168.1.100', 32);
  assert('/32 Network Address tepat', res32.results.networkAddress === '192.168.1.100', res32.results.networkAddress, '192.168.1.100');
  assert('/32 Usable Hosts tepat (1 host route)', res32.results.usableHosts === 1, res32.results.usableHosts, 1);
  assert('/32 Broadcast Address tepat', res32.results.broadcastAddress === '192.168.1.100', res32.results.broadcastAddress, '192.168.1.100');
}

// --- 4. BOUNDARY VALUE ANALYSIS (BVA): PREFIX BATAS KIRI (/0) ---
console.log('\n[Kategori 4: Boundary Value Analysis - Prefix Rendah /0]');
{
  const res0 = SubnetCalculator.calculateSubnet('0.0.0.0', 0);
  assert('/0 Network Address tepat (0.0.0.0)', res0.results.networkAddress === '0.0.0.0', res0.results.networkAddress, '0.0.0.0');
  assert('/0 Broadcast Address tepat (255.255.255.255)', res0.results.broadcastAddress === '255.255.255.255', res0.results.broadcastAddress, '255.255.255.255');
  assert('/0 Total Hosts tepat (4294967296)', res0.results.totalHosts === 4294967296, res0.results.totalHosts, 4294967296);
  assert('/0 Usable Hosts tepat (4294967294)', res0.results.usableHosts === 4294967294, res0.results.usableHosts, 4294967294);
}

// --- 5. FORMAT INPUT KOMBINASI CIDR (e.g. 192.168.10.25/26) ---
console.log('\n[Kategori 5: Parsing Gabungan Format CIDR]');
{
  const resCidr = SubnetCalculator.calculateSubnet('192.168.10.70/26');
  assert('Parsing CIDR slash notation berhasil', resCidr.success === true, resCidr.success, true);
  assert('Network Address /26 tepat', resCidr.results.networkAddress === '192.168.10.64', resCidr.results.networkAddress, '192.168.10.64');
  assert('Broadcast Address /26 tepat', resCidr.results.broadcastAddress === '192.168.10.127', resCidr.results.broadcastAddress, '192.168.10.127');
  assert('Usable Hosts /26 tepat (62)', resCidr.results.usableHosts === 62, resCidr.results.usableHosts, 62);
}

// --- 6. NEGATIVE TESTING / ROBUSTNESS VALIDATION ---
console.log('\n[Kategori 6: Pengujian Ketahanan Input (Negative Testing)]');
{
  const testCases = [
    { ip: '256.0.0.1', prefix: 24, desc: 'Oktet melebihi 255' },
    { ip: '-1.0.0.1', prefix: 24, desc: 'Oktet negatif' },
    { ip: '192.168.1', prefix: 24, desc: 'Kurang dari 4 oktet' },
    { ip: '192.168.1.1.1', prefix: 24, desc: 'Lebih dari 4 oktet' },
    { ip: '192.168.abc.1', prefix: 24, desc: 'Oktet berisi huruf' },
    { ip: '', prefix: 24, desc: 'IP kosong' },
    { ip: '192.168. 1.1', prefix: 24, desc: 'IP mengandung spasi' },
    { ip: '192.168.1.1', prefix: -1, desc: 'Prefix negatif' },
    { ip: '192.168.1.1', prefix: 33, desc: 'Prefix melebihi 32' },
    { ip: '192.168.1.1', prefix: 'xyz', desc: 'Prefix bukan angka' }
  ];

  testCases.forEach(tc => {
    const res = SubnetCalculator.calculateSubnet(tc.ip, tc.prefix);
    assert(`Menolak input tidak valid (${tc.desc})`, res.success === false && typeof res.error === 'string', res.success, false);
  });
}

// --- 7. SUBNET DIVISION / FLSM HELPER ---
console.log('\n[Kategori 7: Pembagian Subnet (Subnet Division)]');
{
  const divRes = SubnetCalculator.divideSubnet('192.168.1.0', 24, 26);
  assert('Subnet division /24 ke /26 berhasil', divRes.success === true, divRes.success, true);
  assert('Jumlah subnet yang dihasilkan tepat (4 blok)', divRes.totalSubnets === 4, divRes.totalSubnets, 4);
  assert('Blok subnet pertama benar (192.168.1.0)', divRes.subnets[0].network === '192.168.1.0', divRes.subnets[0].network, '192.168.1.0');
  assert('Blok subnet kedua benar (192.168.1.64)', divRes.subnets[1].network === '192.168.1.64', divRes.subnets[1].network, '192.168.1.64');
  assert('Blok subnet ketiga benar (192.168.1.128)', divRes.subnets[2].network === '192.168.1.128', divRes.subnets[2].network, '192.168.1.128');
  assert('Blok subnet keempat benar (192.168.1.192)', divRes.subnets[3].network === '192.168.1.192', divRes.subnets[3].network, '192.168.1.192');
}

console.log('\n========================================================');
console.log(`HASIL TEST: ${passedTests} LULUS, ${failedTests} GAGAL`);
console.log('========================================================\n');

if (failedTests > 0) {
  process.exit(1);
} else {
  console.log('SEMUA TEST CASE BERHASIL 100%! Logika kalkulator subnet terverifikasi.');
}


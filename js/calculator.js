/**
 * Subnet Calculator Core Engine
 * Modul kalkulasi subnetting IPv4 dengan validasi ketat dan penanganan edge-case.
 * Kompatibel dengan Browser dan Node.js (UMD).
 */

(function (root, factory) {
  if (typeof define === 'function' && define.amd) {
    define([], factory);
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.SubnetCalculator = factory();
  }
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  /**
   * Konversi alamat IP (string) menjadi 32-bit unsigned integer
   * @param {string} ip - e.g. "192.168.1.1"
   * @returns {number}
   */
  function ipToLong(ip) {
    const octets = ip.split('.').map(Number);
    return ((octets[0] << 24) | (octets[1] << 16) | (octets[2] << 8) | octets[3]) >>> 0;
  }

  /**
   * Konversi 32-bit unsigned integer menjadi format string IP dotted-decimal
   * @param {number} longVal
   * @returns {string}
   */
  function longToIp(longVal) {
    return [
      (longVal >>> 24) & 255,
      (longVal >>> 16) & 255,
      (longVal >>> 8) & 255,
      longVal & 255
    ].join('.');
  }

  /**
   * Format bilangan 32-bit menjadi representasi biner 4 oktet terpisah titik
   * @param {number} longVal
   * @returns {string} e.g. "11000000.10101000.00000001.00000001"
   */
  function longToBinary(longVal) {
    const octets = [
      (longVal >>> 24) & 255,
      (longVal >>> 16) & 255,
      (longVal >>> 8) & 255,
      longVal & 255
    ];
    return octets.map(function (octet) {
      return ('00000000' + octet.toString(2)).slice(-8);
    }).join('.');
  }

  /**
   * Konversi prefix CIDR (0-32) menjadi 32-bit subnet mask integer
   * @param {number} prefix
   * @returns {number}
   */
  function prefixToMaskLong(prefix) {
    if (prefix === 0) return 0;
    if (prefix === 32) return 0xFFFFFFFF >>> 0;
    return (0xFFFFFFFF << (32 - prefix)) >>> 0;
  }

  /**
   * Validasi format alamat IPv4
   * @param {string} ip
   * @returns {{isValid: boolean, error: string|null, sanitizedIp?: string}}
   */
  function validateIp(ip) {
    if (typeof ip !== 'string') {
      return { isValid: false, error: 'Alamat IP harus berupa teks (string).' };
    }

    const trimmed = ip.trim();
    if (trimmed === '') {
      return { isValid: false, error: 'Alamat IP tidak boleh kosong.' };
    }

    // Periksa jika ada spasi di dalam
    if (/\s/.test(trimmed)) {
      return { isValid: false, error: 'Alamat IP tidak boleh mengandung spasi.' };
    }

    const parts = trimmed.split('.');
    if (parts.length !== 4) {
      return {
        isValid: false,
        error: 'Alamat IP harus terdiri dari tepat 4 oktet yang dipisahkan titik (contoh: 192.168.1.1).'
      };
    }

    const sanitizedOctets = [];

    for (let i = 0; i < 4; i++) {
      const part = parts[i];
      if (part === '') {
        return {
          isValid: false,
          error: `Oktet ke-${i + 1} kosong. Format harus X.X.X.X`
        };
      }

      // Periksa apakah hanya berisi angka
      if (!/^\d+$/.test(part)) {
        return {
          isValid: false,
          error: `Oktet ke-${i + 1} ('${part}') bukan angka yang valid.`
        };
      }

      // Cegah leading zeros berlebih (misal 001) kecuali angka 0 itu sendiri
      if (part.length > 1 && part.startsWith('0')) {
        // Warning atau normalisasi ke integer
      }

      const num = parseInt(part, 10);
      if (isNaN(num)) {
        return {
          isValid: false,
          error: `Oktet ke-${i + 1} tidak dapat dikonversi ke angka.`
        };
      }

      if (num < 0 || num > 255) {
        return {
          isValid: false,
          error: `Oktet ke-${i + 1} bernilai ${num}, melebihi batas yang diperbolehkan (0 - 255).`
        };
      }

      sanitizedOctets.push(num);
    }

    return {
      isValid: true,
      error: null,
      sanitizedIp: sanitizedOctets.join('.')
    };
  }

  /**
   * Validasi prefix CIDR (0-32)
   * @param {number|string} prefix
   * @returns {{isValid: boolean, error: string|null, prefixNum?: number}}
   */
  function validatePrefix(prefix) {
    if (prefix === undefined || prefix === null || prefix === '') {
      return { isValid: false, error: 'Prefix subnet tidak boleh kosong.' };
    }

    const strPrefix = String(prefix).trim().replace(/^\//, ''); // Hapus tanda slash jika ada

    if (!/^\d+$/.test(strPrefix)) {
      return { isValid: false, error: 'Prefix harus berupa bilangan bulat positif antara 0 sampai 32.' };
    }

    const num = parseInt(strPrefix, 10);
    if (isNaN(num) || num < 0 || num > 32) {
      return {
        isValid: false,
        error: `Prefix /${strPrefix} tidak valid. Prefix harus berada dalam rentang 0 sampai 32.`
      };
    }

    return {
      isValid: true,
      error: null,
      prefixNum: num
    };
  }

  /**
   * Deteksi Kelas IP (Classful: A, B, C, D, E)
   * @param {string} ip
   * @returns {{className: string, defaultMask: string, defaultPrefix: number, description: string}}
   */
  function getIpClass(ip) {
    const firstOctet = parseInt(ip.split('.')[0], 10);

    if (firstOctet >= 0 && firstOctet <= 127) {
      return {
        className: 'Kelas A',
        defaultMask: '255.0.0.0',
        defaultPrefix: 8,
        description: 'Jaringan skala sangat besar (0.0.0.0 - 127.255.255.255)'
      };
    } else if (firstOctet >= 128 && firstOctet <= 191) {
      return {
        className: 'Kelas B',
        defaultMask: '255.255.0.0',
        defaultPrefix: 16,
        description: 'Jaringan skala menengah ke besar (128.0.0.0 - 191.255.255.255)'
      };
    } else if (firstOctet >= 192 && firstOctet <= 223) {
      return {
        className: 'Kelas C',
        defaultMask: '255.255.255.0',
        defaultPrefix: 24,
        description: 'Jaringan skala kecil hingga LAN lokal (192.0.0.0 - 223.255.255.255)'
      };
    } else if (firstOctet >= 224 && firstOctet <= 239) {
      return {
        className: 'Kelas D (Multicast)',
        defaultMask: 'N/A',
        defaultPrefix: 4,
        description: 'Direservasi untuk Multicast (224.0.0.0 - 239.255.255.255)'
      };
    } else {
      return {
        className: 'Kelas E (Eksperimental)',
        defaultMask: 'N/A',
        defaultPrefix: 4,
        description: 'Direservasi untuk riset & eksperimental (240.0.0.0 - 255.255.255.255)'
      };
    }
  }

  /**
   * Tentukan Scope / Tipe Alamat IP (Private, Public, Loopback, dll)
   * @param {string} ip
   * @returns {{type: string, isPrivate: boolean, note: string}}
   */
  function getIpScope(ip) {
    const octets = ip.split('.').map(Number);
    const o1 = octets[0];
    const o2 = octets[1];

    if (o1 === 10) {
      return { type: 'Private (RFC 1918)', isPrivate: true, note: 'Alamat privat Class A (10.0.0.0/8)' };
    }
    if (o1 === 172 && o2 >= 16 && o2 <= 31) {
      return { type: 'Private (RFC 1918)', isPrivate: true, note: 'Alamat privat Class B (172.16.0.0/12)' };
    }
    if (o1 === 192 && o2 === 168) {
      return { type: 'Private (RFC 1918)', isPrivate: true, note: 'Alamat privat Class C (192.168.0.0/16)' };
    }
    if (o1 === 127) {
      return { type: 'Loopback (RFC 1122)', isPrivate: true, note: 'Localhost / loopback adapter (127.0.0.0/8)' };
    }
    if (o1 === 169 && o2 === 254) {
      return { type: 'Link-Local / APIPA (RFC 3927)', isPrivate: true, note: 'Auto-configuration (169.254.0.0/16)' };
    }
    if (o1 === 100 && o2 >= 64 && o2 <= 127) {
      return { type: 'Shared Address Space / CGNAT (RFC 6598)', isPrivate: true, note: 'Carrier-Grade NAT (100.64.0.0/10)' };
    }
    if (o1 >= 224 && o1 <= 239) {
      return { type: 'Multicast (RFC 5771)', isPrivate: false, note: 'Grup multicast' };
    }
    if (o1 >= 240 && o1 <= 255) {
      return { type: 'Reserved (RFC 1112)', isPrivate: false, note: 'Direservasi untuk masa depan / broadcast' };
    }
    if (o1 === 0) {
      return { type: 'Current Network (RFC 1122)', isPrivate: false, note: 'Jaringan lokal saat ini' };
    }

    return { type: 'Public Internet', isPrivate: false, note: 'Alamat IP Publik yang dapat dirouting di internet' };
  }

  /**
   * Fungsi Utama Kalkulasi Subnet
   * @param {string} ipInput - e.g. "192.168.1.55" atau "192.168.1.55/24"
   * @param {number|string} [prefixInput] - e.g. 24 (opsional jika ipInput sudah menyertakan CIDR)
   * @returns {Object} Hasil kalkulasi lengkap atau error
   */
  function calculateSubnet(ipInput, prefixInput) {
    let rawIp = ipInput;
    let rawPrefix = prefixInput;

    // Dukungan input format gabungan "192.168.1.1/24"
    if (typeof rawIp === 'string' && rawIp.includes('/')) {
      const parts = rawIp.split('/');
      rawIp = parts[0];
      if (rawPrefix === undefined || rawPrefix === null || rawPrefix === '') {
        rawPrefix = parts[1];
      }
    }

    // Validasi IP
    const ipValidation = validateIp(rawIp);
    if (!ipValidation.isValid) {
      return { success: false, error: ipValidation.error };
    }
    const ip = ipValidation.sanitizedIp;

    // Validasi Prefix
    const prefixValidation = validatePrefix(rawPrefix);
    if (!prefixValidation.isValid) {
      return { success: false, error: prefixValidation.error };
    }
    const prefix = prefixValidation.prefixNum;

    // Kalkulasi matematika biner
    const ipLong = ipToLong(ip);
    const maskLong = prefixToMaskLong(prefix);
    const wildcardLong = (~maskLong) >>> 0;
    const netLong = (ipLong & maskLong) >>> 0;
    const bcastLong = (netLong | wildcardLong) >>> 0;

    const subnetMask = longToIp(maskLong);
    const wildcardMask = longToIp(wildcardLong);
    const networkAddress = longToIp(netLong);
    const broadcastAddress = longToIp(bcastLong);

    // Total Host Address
    const totalHosts = prefix === 0 ? 4294967296 : Math.pow(2, 32 - prefix);

    // Usable Hosts & Range Logic
    let usableHosts = 0;
    let firstHost = null;
    let lastHost = null;
    let hostRangeText = '';
    let specialNote = '';

    if (prefix === 32) {
      // /32: Host route tunggal (biasa untuk loopback atau VPN host route)
      usableHosts = 1;
      firstHost = networkAddress;
      lastHost = networkAddress;
      hostRangeText = `${networkAddress} (Host tunggal)`;
      specialNote = 'Prefix /32 merepresentasikan 1 host tunggal (Host Route). Alamat network, broadcast, dan host adalah sama.';
    } else if (prefix === 31) {
      // /31: Point-to-Point link (RFC 3021)
      usableHosts = 2;
      firstHost = networkAddress;
      lastHost = broadcastAddress;
      hostRangeText = `${firstHost} - ${lastHost}`;
      specialNote = 'Prefix /31 menggunakan standar RFC 3021 (Point-to-Point links), di mana network dan broadcast address dapat digunakan langsung sebagai host.';
    } else if (prefix === 0) {
      // /0: Seluruh internet (Default Route 0.0.0.0/0)
      usableHosts = 4294967294; // 2^32 - 2
      firstHost = '0.0.0.1';
      lastHost = '255.255.255.254';
      hostRangeText = `${firstHost} - ${lastHost}`;
      specialNote = 'Prefix /0 merepresentasikan rute default (seluruh ruang alamat IPv4).';
    } else {
      // /1 sampai /30 standar
      usableHosts = Math.pow(2, 32 - prefix) - 2;
      const firstLong = (netLong + 1) >>> 0;
      const lastLong = (bcastLong - 1) >>> 0;
      firstHost = longToIp(firstLong);
      lastHost = longToIp(lastLong);
      hostRangeText = `${firstHost} - ${lastHost}`;
    }

    // Informasi Kelas & Scope
    const ipClass = getIpClass(ip);
    const ipScope = getIpScope(ip);

    // Representasi Biner
    const binary = {
      ip: longToBinary(ipLong),
      subnetMask: longToBinary(maskLong),
      wildcardMask: longToBinary(wildcardLong),
      networkAddress: longToBinary(netLong),
      broadcastAddress: longToBinary(bcastLong),
      networkBits: prefix,
      hostBits: 32 - prefix
    };

    return {
      success: true,
      input: {
        ip: ip,
        prefix: prefix,
        cidr: `${ip}/${prefix}`
      },
      results: {
        networkAddress: networkAddress,
        broadcastAddress: broadcastAddress,
        firstUsableHost: firstHost,
        lastUsableHost: lastHost,
        hostRange: hostRangeText,
        usableHosts: usableHosts,
        usableHostsFormatted: usableHosts.toLocaleString('id-ID'),
        totalHosts: totalHosts,
        totalHostsFormatted: totalHosts.toLocaleString('id-ID'),
        subnetMask: subnetMask,
        wildcardMask: wildcardMask,
        cidrNotation: `/${prefix}`,
        fullCidr: `${networkAddress}/${prefix}`,
        ipClass: ipClass.className,
        ipClassDescription: ipClass.description,
        ipType: ipScope.type,
        ipTypeNote: ipScope.note,
        isPrivate: ipScope.isPrivate,
        specialNote: specialNote,
        binary: binary
      }
    };
  }

  /**
   * Helper untuk membagi subnet menjadi blok lebih kecil (Subnet Breakdown)
   * Misal: /24 dibagi menjadi blok-blok /26
   * @param {string} baseNetwork - e.g. "192.168.1.0"
   * @param {number} currentPrefix - e.g. 24
   * @param {number} newPrefix - e.g. 26
   * @param {number} [limit=16] - Batas maksimal tampilan subnet
   */
  function divideSubnet(baseNetwork, currentPrefix, newPrefix, limit) {
    limit = limit || 32;
    if (newPrefix <= currentPrefix || newPrefix > 32) {
      return { success: false, error: 'Prefix baru harus lebih besar dari prefix saat ini dan maksimal 32.' };
    }

    const netValidation = validateIp(baseNetwork);
    if (!netValidation.isValid) return { success: false, error: netValidation.error };

    const netLong = (ipToLong(netValidation.sanitizedIp) & prefixToMaskLong(currentPrefix)) >>> 0;
    const numSubnets = Math.pow(2, newPrefix - currentPrefix);
    const subnets = [];
    const step = Math.pow(2, 32 - newPrefix);

    const count = Math.min(numSubnets, limit);
    for (let i = 0; i < count; i++) {
      const subNetLong = (netLong + (i * step)) >>> 0;
      const subResult = calculateSubnet(longToIp(subNetLong), newPrefix);
      if (subResult.success) {
        subnets.push({
          index: i + 1,
          network: subResult.results.networkAddress,
          cidr: `${subResult.results.networkAddress}/${newPrefix}`,
          hostRange: subResult.results.hostRange,
          broadcast: subResult.results.broadcastAddress,
          usableHosts: subResult.results.usableHostsFormatted
        });
      }
    }

    return {
      success: true,
      totalSubnets: numSubnets,
      displayedSubnets: count,
      hasMore: numSubnets > count,
      subnets: subnets
    };
  }

  return {
    ipToLong: ipToLong,
    longToIp: longToIp,
    longToBinary: longToBinary,
    prefixToMaskLong: prefixToMaskLong,
    validateIp: validateIp,
    validatePrefix: validatePrefix,
    getIpClass: getIpClass,
    getIpScope: getIpScope,
    calculateSubnet: calculateSubnet,
    divideSubnet: divideSubnet
  };
}));


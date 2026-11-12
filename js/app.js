/**
 * Subnet Calculator Web Application Controller
 * Menghubungkan antarmuka web (UI) dengan SubnetCalculator Engine.
 */

(function () {
  'use strict';

  // --- Elemen DOM ---
  const ipInput = document.getElementById('ipInput');
  const prefixInput = document.getElementById('prefixInput');
  const prefixSelect = document.getElementById('prefixSelect');
  const prefixSlider = document.getElementById('prefixSlider');
  const sliderValDisplay = document.getElementById('sliderValDisplay');
  const autoCalcToggle = document.getElementById('autoCalcToggle');

  const btnCalculate = document.getElementById('btnCalculate');
  const btnReset = document.getElementById('btnReset');
  const btnCopySummary = document.getElementById('btnCopySummary');
  const alertError = document.getElementById('alertError');
  const errorMessage = document.getElementById('errorMessage');

  // Hasil Utama
  const resNetwork = document.getElementById('resNetwork');
  const resBroadcast = document.getElementById('resBroadcast');
  const resHostRange = document.getElementById('resHostRange');
  const resUsableHosts = document.getElementById('resUsableHosts');
  const resTotalHosts = document.getElementById('resTotalHosts');

  // Rincian Teknis
  const resSubnetMask = document.getElementById('resSubnetMask');
  const resWildcardMask = document.getElementById('resWildcardMask');
  const resCidrNotation = document.getElementById('resCidrNotation');
  const resFullCidr = document.getElementById('resFullCidr');
  const resIpClass = document.getElementById('resIpClass');
  const resClassBadge = document.getElementById('resClassBadge');
  const resIpType = document.getElementById('resIpType');
  const resIpTypeNote = document.getElementById('resIpTypeNote');
  const resNetBits = document.getElementById('resNetBits');
  const resHostBits = document.getElementById('resHostBits');
  const lblNetBits = document.getElementById('lblNetBits');
  const lblHostBits = document.getElementById('lblHostBits');
  const bitBarNetwork = document.getElementById('bitBarNetwork');
  const bitBarHost = document.getElementById('bitBarHost');

  // Special Note
  const specialNoteBox = document.getElementById('specialNoteBox');
  const specialNoteText = document.getElementById('specialNoteText');

  // Representasi Biner
  const binIpDec = document.getElementById('binIpDec');
  const binIpBin = document.getElementById('binIpBin');
  const binMaskDec = document.getElementById('binMaskDec');
  const binMaskBin = document.getElementById('binMaskBin');
  const binWildDec = document.getElementById('binWildDec');
  const binWildBin = document.getElementById('binWildBin');
  const binNetDec = document.getElementById('binNetDec');
  const binNetBin = document.getElementById('binNetBin');
  const binBcastDec = document.getElementById('binBcastDec');
  const binBcastBin = document.getElementById('binBcastBin');

  // Riwayat & Toast
  const historyList = document.getElementById('historyList');
  const btnClearHistory = document.getElementById('btnClearHistory');
  const toastContainer = document.getElementById('toastContainer');

  // Tema & Tab
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  const themeIcon = document.getElementById('themeIcon');
  const themeText = document.getElementById('themeText');
  const tabButtons = document.querySelectorAll('.nav-tabs .tab-btn');
  const tabContents = {
    calculator: document.getElementById('tab-calculator'),
    division: document.getElementById('tab-division'),
    sqa: document.getElementById('tab-sqa')
  };

  // FLSM Elements
  const flsmBaseNetwork = document.getElementById('flsmBaseNetwork');
  const flsmTargetPrefix = document.getElementById('flsmTargetPrefix');
  const btnDivideSubnet = document.getElementById('btnDivideSubnet');
  const flsmSummary = document.getElementById('flsmSummary');
  const flsmTableBody = document.getElementById('flsmTableBody');

  // SQA Runner Elements
  const btnRunSqaTests = document.getElementById('btnRunSqaTests');
  const sqaStatTotal = document.getElementById('sqaStatTotal');
  const sqaStatPass = document.getElementById('sqaStatPass');
  const sqaStatFail = document.getElementById('sqaStatFail');
  const sqaStatTime = document.getElementById('sqaStatTime');
  const sqaTestList = document.getElementById('sqaTestList');

  // State
  let lastValidCalculation = null;

  // --- 1. Inisialisasi Pilihan Prefix CIDR ---
  function initPrefixSelect() {
    prefixSelect.innerHTML = '';
    for (let p = 32; p >= 0; p--) {
      const maskLong = SubnetCalculator.prefixToMaskLong(p);
      const maskStr = SubnetCalculator.longToIp(maskLong);
      let hostStr = '';
      if (p === 32) hostStr = '1 host';
      else if (p === 31) hostStr = '2 hosts (RFC 3021)';
      else if (p === 0) hostStr = '4.294.967.294 hosts';
      else {
        const usable = Math.pow(2, 32 - p) - 2;
        hostStr = `${usable.toLocaleString('id-ID')} hosts`;
      }

      const opt = document.createElement('option');
      opt.value = p;
      opt.textContent = `/${p} - ${maskStr} (${hostStr})`;
      if (p === 24) opt.selected = true;
      prefixSelect.appendChild(opt);
    }
  }

  // --- 2. Sinkronisasi Kontrol Prefix (Input, Dropdown, Slider) ---
  function setPrefixValue(newPrefix, source) {
    let p = parseInt(newPrefix, 10);
    if (isNaN(p)) return;
    if (p < 0) p = 0;
    if (p > 32) p = 32;

    if (source !== 'input') prefixInput.value = p;
    if (source !== 'select') prefixSelect.value = p;
    if (source !== 'slider') prefixSlider.value = p;
    sliderValDisplay.textContent = p;

    if (autoCalcToggle.checked) {
      performCalculation();
    }
  }

  // --- 3. Parsing Format Gabungan CIDR (e.g. 192.168.1.1/24) ---
  function checkAndHandleCidrInput() {
    const val = ipInput.value.trim();
    if (val.includes('/')) {
      const parts = val.split('/');
      const parsedIp = parts[0].trim();
      const parsedPrefix = parts[1].trim();

      if (parsedPrefix !== '' && !isNaN(parseInt(parsedPrefix, 10))) {
        setPrefixValue(parsedPrefix, 'all');
      }
    }
  }

  // --- 4. Tampilkan Toast Notifikasi ---
  function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `<span>✔</span> <span>${message}</span>`;
    toastContainer.appendChild(toast);

    setTimeout(function () {
      toast.style.transition = 'opacity 300ms ease, transform 300ms ease';
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(function () {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 300);
    }, 2400);
  }

  // --- 5. Tampilkan / Sembunyikan Error ---
  function showError(msg) {
    errorMessage.textContent = msg;
    alertError.classList.add('show');
    ipInput.style.borderColor = 'var(--danger)';
  }

  function clearError() {
    alertError.classList.remove('show');
    ipInput.style.borderColor = '';
  }

  // --- 6. Eksekusi Kalkulasi Subnet ---
  function performCalculation() {
    checkAndHandleCidrInput();

    let rawIp = ipInput.value.trim();
    let rawPrefix = prefixInput.value.trim();

    if (rawIp.includes('/')) {
      const parts = rawIp.split('/');
      rawIp = parts[0].trim();
      if (!rawPrefix && parts[1]) rawPrefix = parts[1].trim();
    }

    const result = SubnetCalculator.calculateSubnet(rawIp, rawPrefix);

    if (!result.success) {
      showError(result.error);
      return;
    }

    clearError();
    lastValidCalculation = result;

    // Tampilkan Hasil Utama
    resNetwork.textContent = result.results.networkAddress;
    resBroadcast.textContent = result.results.broadcastAddress;
    resHostRange.textContent = result.results.hostRange;
    resUsableHosts.textContent = result.results.usableHostsFormatted;
    resTotalHosts.textContent = result.results.totalHostsFormatted;

    // Tampilkan Rincian Teknis
    resSubnetMask.textContent = result.results.subnetMask;
    resWildcardMask.textContent = result.results.wildcardMask;
    resCidrNotation.textContent = result.results.cidrNotation;
    resFullCidr.textContent = result.results.fullCidr;
    resIpClass.textContent = result.results.ipClass;
    resClassBadge.textContent = result.results.ipClass;

    resIpType.textContent = result.results.ipType;
    if (result.results.isPrivate) {
      resIpType.className = 'badge badge-private';
    } else {
      resIpType.className = 'badge badge-public';
    }
    resIpTypeNote.textContent = result.results.ipTypeNote;

    // Bit Pembagian
    const netBits = result.results.binary.networkBits;
    const hostBits = result.results.binary.hostBits;
    resNetBits.textContent = netBits;
    resHostBits.textContent = hostBits;
    lblNetBits.textContent = netBits;
    lblHostBits.textContent = hostBits;

    const netPercent = (netBits / 32) * 100;
    const hostPercent = 100 - netPercent;
    bitBarNetwork.style.width = `${netPercent}%`;
    bitBarNetwork.textContent = netPercent > 12 ? `${netBits} Net Bits` : `${netBits}`;
    bitBarHost.style.width = `${hostPercent}%`;
    bitBarHost.textContent = hostPercent > 12 ? `${hostBits} Host Bits` : `${hostBits}`;

    // Special Note Banner
    if (result.results.specialNote) {
      specialNoteText.textContent = `ℹ ${result.results.specialNote}`;
      specialNoteBox.classList.add('show');
    } else {
      specialNoteBox.classList.remove('show');
    }

    // Representasi Biner
    binIpDec.textContent = result.input.ip;
    binIpBin.textContent = result.results.binary.ip;
    binMaskDec.textContent = result.results.subnetMask;
    binMaskBin.textContent = result.results.binary.subnetMask;
    binWildDec.textContent = result.results.wildcardMask;
    binWildBin.textContent = result.results.binary.wildcardMask;
    binNetDec.textContent = result.results.networkAddress;
    binNetBin.textContent = result.results.binary.networkAddress;
    binBcastDec.textContent = result.results.broadcastAddress;
    binBcastBin.textContent = result.results.binary.broadcastAddress;

    // Perbarui opsi pembagian subnet (FLSM)
    updateFlsmOptions(result);

    // Simpan ke Riwayat
    saveHistory(result.input.ip, result.input.prefix);
  }

  // --- 7. Riwayat (LocalStorage) ---
  const HISTORY_KEY = 'subnet_calc_history_v1';

  function getHistory() {
    try {
      const data = localStorage.getItem(HISTORY_KEY);
      return data ? JSON.parse(data) : [];
    } catch (e) {
      return [];
    }
  }

  function saveHistory(ip, prefix) {
    const list = getHistory();
    const item = `${ip}/${prefix}`;
    const filtered = list.filter(function (x) { return x !== item; });
    filtered.unshift(item);
    if (filtered.length > 8) filtered.pop();

    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(filtered));
      renderHistory();
    } catch (e) {}
  }

  function renderHistory() {
    const list = getHistory();
    historyList.innerHTML = '';
    if (list.length === 0) {
      historyList.innerHTML = '<span style="color: var(--text-muted); font-size: 0.85rem;">Belum ada riwayat kalkulasi.</span>';
      return;
    }

    list.forEach(function (item) {
      const parts = item.split('/');
      const chip = document.createElement('button');
      chip.className = 'history-chip';
      chip.textContent = item;
      chip.addEventListener('click', function () {
        ipInput.value = parts[0];
        setPrefixValue(parts[1], 'all');
        performCalculation();
      });
      historyList.appendChild(chip);
    });
  }

  function clearHistory() {
    try {
      localStorage.removeItem(HISTORY_KEY);
      renderHistory();
      showToast('Riwayat berhasil dihapus');
    } catch (e) {}
  }

  // --- 8. Fitur Pembagian Subnet FLSM ---
  function updateFlsmOptions(currentResult) {
    flsmBaseNetwork.textContent = currentResult.results.fullCidr;
    flsmTargetPrefix.innerHTML = '';

    const currentP = currentResult.input.prefix;
    if (currentP >= 32) {
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = 'Prefix /32 tidak dapat dibagi lagi';
      flsmTargetPrefix.appendChild(opt);
      btnDivideSubnet.disabled = true;
      return;
    }

    btnDivideSubnet.disabled = false;
    for (let p = currentP + 1; p <= Math.min(30, currentP + 8); p++) {
      const count = Math.pow(2, p - currentP);
      const opt = document.createElement('option');
      opt.value = p;
      opt.textContent = `/${p} (${count} subnet, ${Math.pow(2, 32 - p) - 2} usable hosts/subnet)`;
      flsmTargetPrefix.appendChild(opt);
    }
  }

  function handleDivideSubnet() {
    if (!lastValidCalculation) return;

    const baseNet = lastValidCalculation.results.networkAddress;
    const currentP = lastValidCalculation.input.prefix;
    const targetP = parseInt(flsmTargetPrefix.value, 10);

    if (isNaN(targetP)) return;

    const divResult = SubnetCalculator.divideSubnet(baseNet, currentP, targetP, 32);
    if (!divResult.success) {
      flsmSummary.textContent = divResult.error;
      return;
    }

    flsmSummary.innerHTML = `Membagi <strong>${baseNet}/${currentP}</strong> menjadi <strong>${divResult.totalSubnets.toLocaleString('id-ID')} subnet /${targetP}</strong>:`;
    flsmTableBody.innerHTML = '';

    divResult.subnets.forEach(function (sub) {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${sub.index}</td>
        <td style="color: var(--primary); font-weight: 700;">${sub.cidr}</td>
        <td>${sub.hostRange}</td>
        <td>${sub.broadcast}</td>
        <td>${sub.usableHosts}</td>
      `;
      flsmTableBody.appendChild(tr);
    });
  }

  // --- 9. In-Browser SQA Automated Test Runner ---
  function runSqaInBrowser() {
    const startTime = performance.now();
    let total = 0;
    let passed = 0;
    let failed = 0;
    const testItems = [];

    function testAssert(category, desc, cond, expected, actual) {
      total++;
      if (cond) {
        passed++;
        testItems.push({ category: category, desc: desc, status: 'PASS' });
      } else {
        failed++;
        testItems.push({ category: category, desc: desc, status: 'FAIL', expected: expected, actual: actual });
      }
    }

    // 1. Standard Class C /24
    {
      const r = SubnetCalculator.calculateSubnet('192.168.1.15', 24);
      testAssert('Class C Standar', 'Kalkulasi 192.168.1.15/24 sukses', r.success === true);
      testAssert('Class C Standar', 'Network Address = 192.168.1.0', r.results.networkAddress === '192.168.1.0');
      testAssert('Class C Standar', 'Broadcast Address = 192.168.1.255', r.results.broadcastAddress === '192.168.1.255');
      testAssert('Class C Standar', 'Host Pertama = 192.168.1.1', r.results.firstUsableHost === '192.168.1.1');
      testAssert('Class C Standar', 'Host Terakhir = 192.168.1.254', r.results.lastUsableHost === '192.168.1.254');
      testAssert('Class C Standar', 'Usable Hosts = 254', r.results.usableHosts === 254);
      testAssert('Class C Standar', 'Total Hosts = 256', r.results.totalHosts === 256);
      testAssert('Class C Standar', 'Subnet Mask = 255.255.255.0', r.results.subnetMask === '255.255.255.0');
      testAssert('Class C Standar', 'Wildcard = 0.0.0.255', r.results.wildcardMask === '0.0.0.255');
      testAssert('Class C Standar', 'Kelas IP = Kelas C', r.results.ipClass === 'Kelas C');
      testAssert('Class C Standar', 'Deteksi Private IP', r.results.isPrivate === true);
    }

    // 2. Class B & Class A
    {
      const rB = SubnetCalculator.calculateSubnet('172.16.50.88', 16);
      testAssert('Class B & A', 'Class B Network = 172.16.0.0', rB.results.networkAddress === '172.16.0.0');
      testAssert('Class B & A', 'Class B Broadcast = 172.16.255.255', rB.results.broadcastAddress === '172.16.255.255');
      testAssert('Class B & A', 'Class B Usable Hosts = 65534', rB.results.usableHosts === 65534);

      const rA = SubnetCalculator.calculateSubnet('10.20.30.40', 8);
      testAssert('Class B & A', 'Class A Network = 10.0.0.0', rA.results.networkAddress === '10.0.0.0');
      testAssert('Class B & A', 'Class A Broadcast = 10.255.255.255', rA.results.broadcastAddress === '10.255.255.255');
      testAssert('Class B & A', 'Class A Usable Hosts = 16777214', rA.results.usableHosts === 16777214);
    }

    // 3. Boundary Value Analysis (BVA): /30, /31, /32
    {
      const r30 = SubnetCalculator.calculateSubnet('192.168.1.13', 30);
      testAssert('BVA Prefix Tinggi', '/30 Network Address = 192.168.1.12', r30.results.networkAddress === '192.168.1.12');
      testAssert('BVA Prefix Tinggi', '/30 Broadcast = 192.168.1.15', r30.results.broadcastAddress === '192.168.1.15');
      testAssert('BVA Prefix Tinggi', '/30 Usable Hosts = 2', r30.results.usableHosts === 2);

      const r31 = SubnetCalculator.calculateSubnet('10.0.0.2', 31);
      testAssert('BVA Prefix Tinggi', '/31 Network Address = 10.0.0.2', r31.results.networkAddress === '10.0.0.2');
      testAssert('BVA Prefix Tinggi', '/31 Broadcast = 10.0.0.3', r31.results.broadcastAddress === '10.0.0.3');
      testAssert('BVA Prefix Tinggi', '/31 Usable Hosts (RFC 3021) = 2', r31.results.usableHosts === 2);

      const r32 = SubnetCalculator.calculateSubnet('192.168.1.100', 32);
      testAssert('BVA Prefix Tinggi', '/32 Network Address = 192.168.1.100', r32.results.networkAddress === '192.168.1.100');
      testAssert('BVA Prefix Tinggi', '/32 Broadcast = 192.168.1.100', r32.results.broadcastAddress === '192.168.1.100');
      testAssert('BVA Prefix Tinggi', '/32 Usable Hosts = 1', r32.results.usableHosts === 1);
    }

    // 4. Boundary Value Analysis: /0
    {
      const r0 = SubnetCalculator.calculateSubnet('0.0.0.0', 0);
      testAssert('BVA Prefix Rendah', '/0 Network Address = 0.0.0.0', r0.results.networkAddress === '0.0.0.0');
      testAssert('BVA Prefix Rendah', '/0 Broadcast = 255.255.255.255', r0.results.broadcastAddress === '255.255.255.255');
      testAssert('BVA Prefix Rendah', '/0 Total Hosts = 4294967296', r0.results.totalHosts === 4294967296);
      testAssert('BVA Prefix Rendah', '/0 Usable Hosts = 4294967294', r0.results.usableHosts === 4294967294);
    }

    // 5. CIDR Notation Parsing
    {
      const rC = SubnetCalculator.calculateSubnet('192.168.10.70/26');
      testAssert('CIDR Parsing', 'Parsing IP/Prefix gabungan sukses', rC.success === true);
      testAssert('CIDR Parsing', '/26 Network = 192.168.10.64', rC.results.networkAddress === '192.168.10.64');
      testAssert('CIDR Parsing', '/26 Broadcast = 192.168.10.127', rC.results.broadcastAddress === '192.168.10.127');
      testAssert('CIDR Parsing', '/26 Usable Hosts = 62', rC.results.usableHosts === 62);
    }

    // 6. Negative Testing / Input Robustness
    {
      const negCases = [
        { ip: '256.0.0.1', prefix: 24, desc: 'Oktet 256 melebihi batas 255' },
        { ip: '-1.0.0.1', prefix: 24, desc: 'Oktet bernilai negatif' },
        { ip: '192.168.1', prefix: 24, desc: 'Hanya 3 oktet' },
        { ip: '192.168.1.1.1', prefix: 24, desc: 'Lebih dari 4 oktet' },
        { ip: '192.168.abc.1', prefix: 24, desc: 'Oktet berisi string' },
        { ip: '', prefix: 24, desc: 'Alamat IP kosong' },
        { ip: '192.168. 1.1', prefix: 24, desc: 'IP mengandung spasi' },
        { ip: '192.168.1.1', prefix: -1, desc: 'Prefix negatif' },
        { ip: '192.168.1.1', prefix: 33, desc: 'Prefix melebihi 32' },
        { ip: '192.168.1.1', prefix: 'xyz', desc: 'Prefix bukan angka' }
      ];

      negCases.forEach(function (tc) {
        const nr = SubnetCalculator.calculateSubnet(tc.ip, tc.prefix);
        testAssert('Ketahanan Input (Negative Test)', `Tolak input tidak valid: ${tc.desc}`, nr.success === false && typeof nr.error === 'string');
      });
    }

    // 7. Subnet Division Test
    {
      const d = SubnetCalculator.divideSubnet('192.168.1.0', 24, 26);
      testAssert('Subnet Division', 'Membagi /24 menjadi /26 berhasil', d.success === true);
      testAssert('Subnet Division', 'Jumlah 4 subnet blok', d.totalSubnets === 4);
      testAssert('Subnet Division', 'Blok 1 = 192.168.1.0', d.subnets[0].network === '192.168.1.0');
      testAssert('Subnet Division', 'Blok 2 = 192.168.1.64', d.subnets[1].network === '192.168.1.64');
      testAssert('Subnet Division', 'Blok 3 = 192.168.1.128', d.subnets[2].network === '192.168.1.128');
      testAssert('Subnet Division', 'Blok 4 = 192.168.1.192', d.subnets[3].network === '192.168.1.192');
    }

    const elapsed = Math.round(performance.now() - startTime);

    // Update UI Stats
    sqaStatTotal.textContent = total;
    sqaStatPass.textContent = passed;
    sqaStatFail.textContent = failed;
    sqaStatTime.textContent = `${elapsed} ms`;

    // Render list
    sqaTestList.innerHTML = '';
    testItems.forEach(function (item, idx) {
      const div = document.createElement('div');
      div.className = 'sqa-test-item';
      div.innerHTML = `
        <div>
          <span style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">[${item.category}]</span>
          <span style="margin-left: 8px;">${idx + 1}. ${item.desc}</span>
        </div>
        <span class="sqa-badge ${item.status.toLowerCase()}">${item.status}</span>
      `;
      sqaTestList.appendChild(div);
    });

    showToast(`SQA Suite selesai: ${passed}/${total} test lulus (${elapsed} ms)`);
  }

  // --- 10. Copy Summary Generator ---
  function copySummaryToClipboard() {
    if (!lastValidCalculation) return;

    const r = lastValidCalculation.results;
    const inp = lastValidCalculation.input;

    const summary = [
      '========================================',
      '      RINGKASAN KALKULASI SUBNET IPV4   ',
      '========================================',
      `Input IP/Prefix    : ${inp.cidr}`,
      `Network Address    : ${r.networkAddress}`,
      `Broadcast Address  : ${r.broadcastAddress}`,
      `Rentang Host Usable: ${r.hostRange}`,
      `Jumlah Host Usable : ${r.usableHostsFormatted} host`,
      `Total Alamat IP    : ${r.totalHostsFormatted} alamat`,
      `Subnet Mask        : ${r.subnetMask} (${r.cidrNotation})`,
      `Wildcard Mask      : ${r.wildcardMask}`,
      `Kelas IP           : ${r.ipClass}`,
      `Kategori Scope     : ${r.ipType} (${r.ipTypeNote})`,
      '========================================'
    ].join('\n');

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(summary).then(function () {
        showToast('Ringkasan subnet berhasil disalin ke clipboard!');
      }).catch(function () {
        showToast('Gagal menyalin ringkasan.');
      });
    } else {
      showToast('Clipboard API tidak didukung pada browser ini.');
    }
  }

  // --- 11. Theme Switcher ---
  function initTheme() {
    const savedTheme = localStorage.getItem('subnet_theme') || 'light';
    applyTheme(savedTheme);
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    if (theme === 'dark') {
      themeIcon.textContent = '☀️';
      themeText.textContent = 'Mode Terang';
    } else {
      themeIcon.textContent = '🌙';
      themeText.textContent = 'Mode Gelap';
    }
    localStorage.setItem('subnet_theme', theme);
  }

  function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
  }

  // --- 12. Setup Event Listeners ---
  function setupEventListeners() {
    // Tombol Hitung & Reset
    btnCalculate.addEventListener('click', performCalculation);
    btnReset.addEventListener('click', function () {
      ipInput.value = '192.168.1.10';
      setPrefixValue(24, 'all');
      clearError();
      performCalculation();
      showToast('Form telah direset ke nilai bawaan.');
    });

    // Salin Ringkasan
    btnCopySummary.addEventListener('click', copySummaryToClipboard);

    // Salin Tombol Per Kartu
    document.querySelectorAll('.copy-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const targetId = btn.getAttribute('data-copy');
        const targetEl = document.getElementById(targetId);
        if (targetEl && targetEl.textContent) {
          const val = targetEl.textContent.trim();
          navigator.clipboard.writeText(val).then(function () {
            showToast(`Tersalin: ${val}`);
          });
        }
      });
    });

    // Sinkronisasi Input IP & Prefix
    ipInput.addEventListener('input', function () {
      if (autoCalcToggle.checked) performCalculation();
    });

    ipInput.addEventListener('keypress', function (e) {
      if (e.key === 'Enter') {
        performCalculation();
      }
    });

    prefixInput.addEventListener('input', function () {
      setPrefixValue(prefixInput.value, 'input');
    });

    prefixSelect.addEventListener('change', function () {
      setPrefixValue(prefixSelect.value, 'select');
    });

    prefixSlider.addEventListener('input', function () {
      setPrefixValue(prefixSlider.value, 'slider');
    });

    // Presets
    document.querySelectorAll('.preset-chip').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const ip = btn.getAttribute('data-ip');
        const prefix = btn.getAttribute('data-prefix');
        ipInput.value = ip;
        setPrefixValue(prefix, 'all');
        performCalculation();
      });
    });

    // Riwayat
    btnClearHistory.addEventListener('click', clearHistory);

    // FLSM Division
    btnDivideSubnet.addEventListener('click', handleDivideSubnet);

    // SQA Runner
    btnRunSqaTests.addEventListener('click', runSqaInBrowser);

    // Theme Toggle
    themeToggleBtn.addEventListener('click', toggleTheme);

    // Tab Navigation
    tabButtons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        const target = btn.getAttribute('data-tab');
        tabButtons.forEach(function (b) { b.classList.remove('active'); });
        btn.classList.add('active');

        Object.keys(tabContents).forEach(function (key) {
          if (key === target) {
            tabContents[key].style.display = 'block';
          } else {
            tabContents[key].style.display = 'none';
          }
        });

        if (target === 'sqa' && sqaTestList.children.length === 0) {
          runSqaInBrowser();
        }
      });
    });
  }

  // --- Bootstrapping ---
  function init() {
    initTheme();
    initPrefixSelect();
    setupEventListeners();
    renderHistory();
    performCalculation();
    runSqaInBrowser(); // Pre-run SQA tests so stats are ready
  }

  // Jalankan saat DOM siap
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();


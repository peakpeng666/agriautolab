# 干净环境端到端安装记录（§6.1 的证据）

- 日期：2026-08-22；机器：Windows 11 + WSL2
- 净房：全新注册的第二个 Ubuntu-22.04 实例 `agri-clean`（wsl --install Ubuntu-22.04 --name agri-clean --no-launch），
  与开发环境零共享（无预装依赖、无缓存、无 F2C）
- 流程（root，逐字即 §6.1 验收命令）：git clone → bash scripts/install/setup_wsl.sh → 内含 verify_install.sh
- 结果：**EXIT_CODE=0，九项自校验全部 ✅，pytest 530 passed / 30 skipped**

READY

[clean-room] 编译输出：125 个 CXX 目标，逐行省略（完整日志见交付附件）
== AgriAutoLab 一键安装（WSL2 Ubuntu 22.04）==
  运行在 WSL2 内 ✓
  Ubuntu 22.04 ✓
  原生文件系统 ✓
  [01_apt] 缺 19 个包：build-essential cmake doxygen g++ libeigen3-dev libgdal-dev libpython3-dev python3-pip python3-venv python3-matplotlib python3-tk lcov libgtest-dev libtbb-dev swig libgeos-dev gnuplot libtinyxml2-dev nlohmann-json3-dev
Hit:1 http://archive.ubuntu.com/ubuntu jammy InRelease
Hit:2 http://security.ubuntu.com/ubuntu jammy-security InRelease
Hit:3 http://archive.ubuntu.com/ubuntu jammy-updates InRelease
Hit:4 http://archive.ubuntu.com/ubuntu jammy-backports InRelease
Reading package lists...
Reading package lists...
Building dependency tree...
Reading state information...
The following additional packages will be installed:
  aglfn autoconf automake autotools-dev blt bzip2 cmake-data cpp cpp-11 curl
  default-libmysqlclient-dev dh-elpa-helper dpkg-dev emacsen-common fonts-lyx
  g++-11 gcc gcc-11 gcc-11-base gdal-data gnuplot-data gnuplot-qt googletest
  hdf5-helpers icu-devtools libaec-dev libaec0 libaom-dev libaom3 libarchive13
  libarmadillo-dev libarmadillo10 libarpack2 libarpack2-dev libasan6
  libatomic1 libblas3 libblosc-dev libblosc1 libboost-dev libboost1.74-dev
  libc-dev-bin libc6 libc6-dev libcc1-0 libcfitsio-dev libcfitsio9
  libcharls-dev libcharls2 libclang-cpp14 libclang1-14 libcrypt-dev libcurl4
  libcurl4-openssl-dev libdav1d-dev libdav1d5 libde265-0 libde265-dev
  libdeflate-dev libdouble-conversion3 libdpkg-perl libevdev2 libexpat1-dev
  libfreexl-dev libfreexl1 libfyba-dev libfyba0 libgcc-11-dev libgd3 libgdal30
  libgeos-c1v5 libgeos3.10.2 libgeotiff-dev libgeotiff5 libgfortran5
  libgif-dev libgif7 libgomp1 libgudev-1.0-0 libhdf4-0-alt libhdf4-alt-dev
  libhdf5-103-1 libhdf5-cpp-103-1 libhdf5-dev libhdf5-fortran-102
  libhdf5-hl-100 libhdf5-hl-cpp-100 libhdf5-hl-fortran-100 libheif-dev
  libheif1 libice6 libicu-dev libimagequant0 libinput-bin libinput10 libisl23
  libitm1 libjbig-dev libjpeg-dev libjpeg-turbo8-dev libjpeg8-dev libjs-jquery
  libjs-jquery-ui libjs-sphinxdoc libjs-underscore libjson-c-dev libjson-perl
  libjsoncpp25 libkml-dev libkmlbase1 libkmlconvenience1 libkmldom1
  libkmlengine1 libkmlregionator1 libkmlxsd1 liblapack3 liblbfgsb0 libllvm14
  liblsan0 libltdl-dev libltdl7 liblua5.4-0 liblz4-dev liblzma-dev liblzma5
  libmd4c0 libminizip-dev libminizip1 libmpc3 libmtdev1 libmysqlclient-dev
  libmysqlclient21 libnetcdf-dev libnetcdf19 libnotify4 libnsl-dev libnspr4
  libnss3 libodbc2 libodbccr2 libodbcinst2 libogdi-dev libogdi4.1
  libopenblas-dev libopenblas-pthread-dev libopenblas0 libopenblas0-pthread
  libopenjp2-7 libopenjp2-7-dev libpcre2-16-0 libpcre2-32-0 libpcre2-dev
  libpcre2-posix3 libperlio-gzip-perl libpng-dev libpng16-16 libpoppler-dev
  libpoppler-private-dev libpoppler118 libpq-dev libpq5 libproj-dev libproj22
  libpython3.10 libpython3.10-dev libpython3.10-minimal libpython3.10-stdlib
  libqhull-dev libqhull-r8.0 libqhull8.0 libqhullcpp8.0 libqt5core5a
  libqt5dbus5 libqt5gui5 libqt5network5 libqt5printsupport5 libqt5svg5
  libqt5widgets5 libquadmath0 libraqm0 librhash0 librttopo-dev librttopo1
  libsm6 libsnappy1v5 libspatialite-dev libspatialite7 libsqlite3-0
  libsqlite3-dev libssl-dev libssl3 libstdc++-11-dev libsuperlu-dev
  libsuperlu5 libsz2 libtbb12 libtbbmalloc2 libtcl8.6 libtiff-dev libtiff5
  libtiffxx5 libtinyxml2-9 libtirpc-dev libtk8.6 libtsan0 libubsan1
  liburiparser-dev liburiparser1 libwacom-common libwacom9 libwebp-dev
  libwebpdemux2 libwebpmux3 libwxbase3.0-0v5 libwxgtk3.0-gtk3-0v5 libx265-199
  libx265-dev libxapian30 libxcb-icccm4 libxcb-image0 libxcb-keysyms1
  libxcb-render-util0 libxcb-shape0 libxcb-util1 libxcb-xinerama0
  libxcb-xinput0 libxcb-xkb1 libxerces-c-dev libxerces-c3.2 libxft2
  libxkbcommon-x11-0 libxml2 libxml2-dev libxpm4 libxsimd-dev libxslt1.1
  libxss1 libzstd-dev linux-libc-dev lto-disabled-list m4 make mysql-common
  pkg-config proj-data python-matplotlib-data python3-appdirs python3-beniget
  python3-brotli python3-cycler python3-dateutil python3-decorator python3-dev
  python3-fonttools python3-fs python3-gast python3-kiwisolver python3-lxml
  python3-lz4 python3-mpmath python3-numpy python3-packaging python3-pil
  python3-pil.imagetk python3-pip-whl python3-ply python3-pythran
  python3-scipy python3-setuptools-whl python3-sympy python3-ufolib2
  python3-unicodedata2 python3-wheel python3.10 python3.10-dev
  python3.10-minimal python3.10-venv rpcsvc-proto swig4.0 tk8.6-blt2.5
  unicode-data unixodbc-common unixodbc-dev zlib1g-dev
Suggested packages:
  autoconf-archive gnu-standards autoconf-doc libtool gettext blt-demo
  bzip2-doc cmake-doc ninja-build cmake-format cpp-doc gcc-11-locales
  doxygen-latex doxygen-doc doxygen-gui graphviz debian-keyring g++-multilib
  g++-11-multilib gcc-11-doc gcc-multilib manpages-dev flex bison gdb gcc-doc
  gcc-11-multilib gnuplot-doc lrzip libitpp-dev libboost-doc libboost1.74-doc
  libboost-atomic1.74-dev libboost-chrono1.74-dev libboost-container1.74-dev
  libboost-context1.74-dev libboost-contract1.74-dev
  libboost-coroutine1.74-dev libboost-date-time1.74-dev
  libboost-exception1.74-dev libboost-fiber1.74-dev
  libboost-filesystem1.74-dev libboost-graph1.74-dev
  libboost-graph-parallel1.74-dev libboost-iostreams1.74-dev
  libboost-locale1.74-dev libboost-log1.74-dev libboost-math1.74-dev
  libboost-mpi1.74-dev libboost-mpi-python1.74-dev libboost-numpy1.74-dev
  libboost-program-options1.74-dev libboost-python1.74-dev
  libboost-random1.74-dev libboost-regex1.74-dev
  libboost-serialization1.74-dev libboost-stacktrace1.74-dev
  libboost-system1.74-dev libboost-test1.74-dev libboost-thread1.74-dev
  libboost-timer1.74-dev libboost-type-erasure1.74-dev libboost-wave1.74-dev
  libboost1.74-tools-dev libmpfrc++-dev libntl-dev libboost-nowide1.74-dev
  glibc-doc libcurl4-doc libidn11-dev libkrb5-dev libldap2-dev librtmp-dev
  libssh2-1-dev bzr libeigen3-doc libgd-tools libgdal-doc libgeotiff-epsg
  geotiff-bin gdal-bin libhdf4-doc hdf4-tools libhdf5-doc icu-doc
  libjs-jquery-ui-docs libtool-doc liblzma-doc netcdf-bin netcdf-doc
  gnome-shell | notification-daemon odbc-postgresql tdsodbc ogdi-bin
  libfreetype6-dev postgresql-doc-14 proj-bin qt5-image-formats-plugins
  qtwayland5 sqlite3-doc libssl-doc libstdc++-11-doc libsuperlu-doc libtbb-doc
  tcl8.6 tk8.6 libx265-doc xapian-tools libxerces-c-doc libxsimd-doc m4-doc
  make-doc python-cycler-doc python-lxml-doc dvipng ffmpeg fonts-staypuft
  ghostscript gir1.2-gtk-3.0 inkscape ipython3 python-matplotlib-doc
  python3-cairocffi python3-gi-cairo python3-gobject python3-pyqt5 python3-sip
  python3-tornado texlive-extra-utils texlive-latex-extra python-mpmath-doc
  python3-gmpy2 gfortran python-numpy-doc python3-pytest python-pil-doc
  python-ply-doc python-scipy-doc texlive-fonts-extra python-sympy-doc tix
  python3-tk-dbg python3.10-doc binfmt-support swig-doc swig-examples
  swig4.0-examples swig4.0-doc
Recommended packages:
  fakeroot libalgorithm-merge-perl libgd-gd2-perl manpages-dev libc-devtools
  libnss-nis libnss-nisplus libcfitsio-doc libfile-fcntllock-perl proj-bin
  javascript-common libjson-xs-perl libtool libpng-tools poppler-data
  qttranslations5-l10n qt5-gtk-platformtheme libwacom-bin python3-bs4
  python3-html5lib python3-olefile
The following NEW packages will be installed:
  aglfn autoconf automake autotools-dev blt build-essential bzip2 cmake
  cmake-data cpp cpp-11 default-libmysqlclient-dev dh-elpa-helper doxygen
  dpkg-dev emacsen-common fonts-lyx g++ g++-11 gcc gcc-11 gcc-11-base
  gdal-data gnuplot gnuplot-data gnuplot-qt googletest hdf5-helpers
  icu-devtools lcov libaec-dev libaec0 libaom-dev libaom3 libarchive13
  libarmadillo-dev libarmadillo10 libarpack2 libarpack2-dev libasan6
  libatomic1 libblas3 libblosc-dev libblosc1 libboost-dev libboost1.74-dev
  libc-dev-bin libc6-dev libcc1-0 libcfitsio-dev libcfitsio9 libcharls-dev
  libcharls2 libclang-cpp14 libclang1-14 libcrypt-dev libcurl4-openssl-dev
  libdav1d-dev libdav1d5 libde265-0 libde265-dev libdeflate-dev
  libdouble-conversion3 libdpkg-perl libeigen3-dev libevdev2 libexpat1-dev
  libfreexl-dev libfreexl1 libfyba-dev libfyba0 libgcc-11-dev libgd3
  libgdal-dev libgdal30 libgeos-c1v5 libgeos-dev libgeos3.10.2 libgeotiff-dev
  libgeotiff5 libgfortran5 libgif-dev libgif7 libgomp1 libgtest-dev
  libgudev-1.0-0 libhdf4-0-alt libhdf4-alt-dev libhdf5-103-1 libhdf5-cpp-103-1
  libhdf5-dev libhdf5-fortran-102 libhdf5-hl-100 libhdf5-hl-cpp-100
  libhdf5-hl-fortran-100 libheif-dev libheif1 libice6 libicu-dev
  libimagequant0 libinput-bin libinput10 libisl23 libitm1 libjbig-dev
  libjpeg-dev libjpeg-turbo8-dev libjpeg8-dev libjs-jquery libjs-jquery-ui
  libjs-sphinxdoc libjs-underscore libjson-c-dev libjson-perl libjsoncpp25
  libkml-dev libkmlbase1 libkmlconvenience1 libkmldom1 libkmlengine1
  libkmlregionator1 libkmlxsd1 liblapack3 liblbfgsb0 libllvm14 liblsan0
  libltdl-dev libltdl7 liblua5.4-0 liblz4-dev liblzma-dev libmd4c0
  libminizip-dev libminizip1 libmpc3 libmtdev1 libmysqlclient-dev
  libmysqlclient21 libnetcdf-dev libnetcdf19 libnotify4 libnsl-dev libnspr4
  libnss3 libodbc2 libodbccr2 libodbcinst2 libogdi-dev libogdi4.1
  libopenblas-dev libopenblas-pthread-dev libopenblas0 libopenblas0-pthread
  libopenjp2-7 libopenjp2-7-dev libpcre2-16-0 libpcre2-32-0 libpcre2-dev
  libpcre2-posix3 libperlio-gzip-perl libpng-dev libpoppler-dev
  libpoppler-private-dev libpoppler118 libpq-dev libpq5 libproj-dev libproj22
  libpython3-dev libpython3.10-dev libqhull-dev libqhull-r8.0 libqhull8.0
  libqhullcpp8.0 libqt5core5a libqt5dbus5 libqt5gui5 libqt5network5
  libqt5printsupport5 libqt5svg5 libqt5widgets5 libquadmath0 libraqm0
  librhash0 librttopo-dev librttopo1 libsm6 libsnappy1v5 libspatialite-dev
  libspatialite7 libsqlite3-dev libssl-dev libstdc++-11-dev libsuperlu-dev
  libsuperlu5 libsz2 libtbb-dev libtbb12 libtbbmalloc2 libtcl8.6 libtiff-dev
  libtiffxx5 libtinyxml2-9 libtinyxml2-dev libtirpc-dev libtk8.6 libtsan0
  libubsan1 liburiparser-dev liburiparser1 libwacom-common libwacom9
  libwebp-dev libwebpdemux2 libwebpmux3 libwxbase3.0-0v5 libwxgtk3.0-gtk3-0v5
  libx265-199 libx265-dev libxapian30 libxcb-icccm4 libxcb-image0
  libxcb-keysyms1 libxcb-render-util0 libxcb-shape0 libxcb-util1
  libxcb-xinerama0 libxcb-xinput0 libxcb-xkb1 libxerces-c-dev libxerces-c3.2
  libxft2 libxkbcommon-x11-0 libxml2-dev libxpm4 libxsimd-dev libxslt1.1
  libxss1 libzstd-dev linux-libc-dev lto-disabled-list m4 make mysql-common
  nlohmann-json3-dev pkg-config proj-data python-matplotlib-data
  python3-appdirs python3-beniget python3-brotli python3-cycler
  python3-dateutil python3-decorator python3-dev python3-fonttools python3-fs
  python3-gast python3-kiwisolver python3-lxml python3-lz4 python3-matplotlib
  python3-mpmath python3-numpy python3-packaging python3-pil
  python3-pil.imagetk python3-pip python3-pip-whl python3-ply python3-pythran
  python3-scipy python3-setuptools-whl python3-sympy python3-tk
  python3-ufolib2 python3-unicodedata2 python3-venv python3-wheel
  python3.10-dev python3.10-venv rpcsvc-proto swig swig4.0 tk8.6-blt2.5
  unicode-data unixodbc-common unixodbc-dev zlib1g-dev
The following packages will be upgraded:
  curl libc6 libcurl4 liblzma5 libpng16-16 libpython3.10 libpython3.10-minimal
  libpython3.10-stdlib libsqlite3-0 libssl3 libtiff5 libxml2 python3.10
  python3.10-minimal
14 upgraded, 289 newly installed, 0 to remove and 122 not upgraded.
Need to get 318 MB of archives.
After this operation, 1431 MB of additional disk space will be used.
Get:1 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libc6 amd64 2.35-0ubuntu3.14 [3234 kB]
Get:2 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libpython3.10 amd64 3.10.12-1~22.04.16 [1950 kB]
Get:3 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libssl3 amd64 3.0.2-0ubuntu1.26 [1906 kB]
Get:4 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 python3.10 amd64 3.10.12-1~22.04.16 [508 kB]
Get:5 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libpython3.10-stdlib amd64 3.10.12-1~22.04.16 [1850 kB]
Get:6 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 python3.10-minimal amd64 3.10.12-1~22.04.16 [2254 kB]
Get:7 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libpython3.10-minimal amd64 3.10.12-1~22.04.16 [817 kB]
Get:8 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 liblzma5 amd64 5.2.5-2ubuntu1.1 [99.6 kB]
Get:9 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libsqlite3-0 amd64 3.37.2-2ubuntu0.7 [643 kB]
Get:10 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libdouble-conversion3 amd64 3.1.7-4 [39.0 kB]
Get:11 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libpcre2-16-0 amd64 10.39-3ubuntu0.1 [203 kB]
Get:12 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 libqt5core5a amd64 5.15.3+dfsg-2ubuntu0.2 [2006 kB]
Get:13 http://archive.ubuntu.com/ubuntu jammy/main amd64 libice6 amd64 2:1.0.10-1build2 [42.6 kB]
Get:14 http://archive.ubuntu.com/ubuntu jammy/main amd64 libevdev2 amd64 1.12.1+dfsg-1 [39.5 kB]
Get:15 http://archive.ubuntu.com/ubuntu jammy/main amd64 libmtdev1 amd64 1.1.6-1build4 [14.5 kB]
Get:16 http://archive.ubuntu.com/ubuntu jammy/main amd64 libgudev-1.0-0 amd64 1:237-2build1 [16.3 kB]
Get:17 http://archive.ubuntu.com/ubuntu jammy/main amd64 libwacom-common all 2.2.0-1 [54.3 kB]
Get:18 http://archive.ubuntu.com/ubuntu jammy/main amd64 libwacom9 amd64 2.2.0-1 [22.0 kB]
Get:19 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libinput-bin amd64 1.20.0-1ubuntu0.4 [20.4 kB]
Get:20 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libinput10 amd64 1.20.0-1ubuntu0.4 [131 kB]
Get:21 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libmd4c0 amd64 0.4.8-1 [42.0 kB]
Get:22 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libpng16-16 amd64 1.6.37-3ubuntu0.6 [192 kB]
Get:23 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 libqt5dbus5 amd64 5.15.3+dfsg-2ubuntu0.2 [222 kB]
Get:24 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 libqt5network5 amd64 5.15.3+dfsg-2ubuntu0.2 [731 kB]
Get:25 http://archive.ubuntu.com/ubuntu jammy/main amd64 libsm6 amd64 2:1.2.3-1build2 [16.7 kB]
Get:26 http://archive.ubuntu.com/ubuntu jammy/main amd64 libxcb-icccm4 amd64 0.4.1-1.1build2 [11.5 kB]
Get:27 http://archive.ubuntu.com/ubuntu jammy/main amd64 libxcb-util1 amd64 0.4.0-1build2 [11.4 kB]
Get:28 http://archive.ubuntu.com/ubuntu jammy/main amd64 libxcb-image0 amd64 0.4.0-2 [11.5 kB]
Get:29 http://archive.ubuntu.com/ubuntu jammy/main amd64 libxcb-keysyms1 amd64 0.4.0-1build3 [8746 B]
Get:30 http://archive.ubuntu.com/ubuntu jammy/main amd64 libxcb-render-util0 amd64 0.3.9-1build3 [10.3 kB]
Get:31 http://archive.ubuntu.com/ubuntu jammy/main amd64 libxcb-shape0 amd64 1.14-3ubuntu3 [6158 B]
Get:32 http://archive.ubuntu.com/ubuntu jammy/main amd64 libxcb-xinerama0 amd64 1.14-3ubuntu3 [5414 B]
Get:33 http://archive.ubuntu.com/ubuntu jammy/main amd64 libxcb-xinput0 amd64 1.14-3ubuntu3 [34.3 kB]
Get:34 http://archive.ubuntu.com/ubuntu jammy/main amd64 libxcb-xkb1 amd64 1.14-3ubuntu3 [32.8 kB]
Get:35 http://archive.ubuntu.com/ubuntu jammy/main amd64 libxkbcommon-x11-0 amd64 1.4.0-1 [14.4 kB]
Get:36 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 libqt5gui5 amd64 5.15.3+dfsg-2ubuntu0.2 [3722 kB]
Get:37 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 libqt5widgets5 amd64 5.15.3+dfsg-2ubuntu0.2 [2561 kB]
Get:38 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libqt5svg5 amd64 5.15.3-1 [149 kB]
Get:39 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libxml2 amd64 2.9.13+dfsg-1ubuntu0.12 [765 kB]
Get:40 http://archive.ubuntu.com/ubuntu jammy/main amd64 m4 amd64 1.4.18-5ubuntu2 [199 kB]
Get:41 http://archive.ubuntu.com/ubuntu jammy/main amd64 autoconf all 2.71-2 [338 kB]
Get:42 http://archive.ubuntu.com/ubuntu jammy/main amd64 autotools-dev all 20220109.1 [44.9 kB]
Get:43 http://archive.ubuntu.com/ubuntu jammy/main amd64 automake all 1:1.16.5-1.3 [558 kB]
Get:44 http://archive.ubuntu.com/ubuntu jammy/main amd64 libtcl8.6 amd64 8.6.12+dfsg-1build1 [990 kB]
Get:45 http://archive.ubuntu.com/ubuntu jammy/main amd64 libxft2 amd64 2.3.4-1 [41.8 kB]
Get:46 http://archive.ubuntu.com/ubuntu jammy/main amd64 libxss1 amd64 1:1.2.3-1build2 [8476 B]
Get:47 http://archive.ubuntu.com/ubuntu jammy/main amd64 libtk8.6 amd64 8.6.12-1build1 [784 kB]
Get:48 http://archive.ubuntu.com/ubuntu jammy/main amd64 tk8.6-blt2.5 amd64 2.5.3+dfsg-4.1build2 [643 kB]
Get:49 http://archive.ubuntu.com/ubuntu jammy/main amd64 blt amd64 2.5.3+dfsg-4.1build2 [4838 B]
Get:50 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libc-dev-bin amd64 2.35-0ubuntu3.14 [20.3 kB]
Get:51 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 linux-libc-dev amd64 5.15.0-190.200 [1343 kB]
Get:52 http://archive.ubuntu.com/ubuntu jammy/main amd64 libcrypt-dev amd64 1:4.4.27-1 [112 kB]
Get:53 http://archive.ubuntu.com/ubuntu jammy/main amd64 rpcsvc-proto amd64 1.4.2-0ubuntu6 [68.5 kB]
Get:54 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libtirpc-dev amd64 1.3.2-2ubuntu0.1 [192 kB]
Get:55 http://archive.ubuntu.com/ubuntu jammy/main amd64 libnsl-dev amd64 1.3.0-2build2 [71.3 kB]
Get:56 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libc6-dev amd64 2.35-0ubuntu3.14 [2100 kB]
Get:57 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 gcc-11-base amd64 11.4.0-1ubuntu1~22.04.3 [216 kB]
Get:58 http://archive.ubuntu.com/ubuntu jammy/main amd64 libisl23 amd64 0.24-2build1 [727 kB]
Get:59 http://archive.ubuntu.com/ubuntu jammy/main amd64 libmpc3 amd64 1.2.1-2build1 [46.9 kB]
Get:60 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 cpp-11 amd64 11.4.0-1ubuntu1~22.04.3 [10.0 MB]
Get:61 http://archive.ubuntu.com/ubuntu jammy/main amd64 cpp amd64 4:11.2.0-1ubuntu1 [27.7 kB]
Get:62 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libcc1-0 amd64 12.3.0-1ubuntu1~22.04.3 [48.3 kB]
Get:63 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libgomp1 amd64 12.3.0-1ubuntu1~22.04.3 [127 kB]
Get:64 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libitm1 amd64 12.3.0-1ubuntu1~22.04.3 [30.2 kB]
Get:65 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libatomic1 amd64 12.3.0-1ubuntu1~22.04.3 [10.5 kB]
Get:66 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libasan6 amd64 11.4.0-1ubuntu1~22.04.3 [2283 kB]
Get:67 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 liblsan0 amd64 12.3.0-1ubuntu1~22.04.3 [1069 kB]
Get:68 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libtsan0 amd64 11.4.0-1ubuntu1~22.04.3 [2260 kB]
Get:69 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libubsan1 amd64 12.3.0-1ubuntu1~22.04.3 [976 kB]
Get:70 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libquadmath0 amd64 12.3.0-1ubuntu1~22.04.3 [154 kB]
Get:71 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libgcc-11-dev amd64 11.4.0-1ubuntu1~22.04.3 [2517 kB]
Get:72 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 gcc-11 amd64 11.4.0-1ubuntu1~22.04.3 [20.1 MB]
Get:73 http://archive.ubuntu.com/ubuntu jammy/main amd64 gcc amd64 4:11.2.0-1ubuntu1 [5112 B]
Get:74 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libstdc++-11-dev amd64 11.4.0-1ubuntu1~22.04.3 [2101 kB]
Get:75 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 g++-11 amd64 11.4.0-1ubuntu1~22.04.3 [11.4 MB]
Get:76 http://archive.ubuntu.com/ubuntu jammy/main amd64 g++ amd64 4:11.2.0-1ubuntu1 [1412 B]
Get:77 http://archive.ubuntu.com/ubuntu jammy/main amd64 make amd64 4.3-4.1build1 [180 kB]
Get:78 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libdpkg-perl all 1.21.1ubuntu2.6 [237 kB]
Get:79 http://archive.ubuntu.com/ubuntu jammy/main amd64 bzip2 amd64 1.0.8-5build1 [34.8 kB]
Get:80 http://archive.ubuntu.com/ubuntu jammy/main amd64 lto-disabled-list all 24 [12.5 kB]
Get:81 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 dpkg-dev all 1.21.1ubuntu2.6 [922 kB]
Get:82 http://archive.ubuntu.com/ubuntu jammy/main amd64 build-essential amd64 12.9ubuntu3 [4744 B]
Get:83 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libarchive13 amd64 3.6.0-1ubuntu1.8 [368 kB]
Get:84 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 curl amd64 7.81.0-1ubuntu1.26 [194 kB]
Get:85 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libcurl4 amd64 7.81.0-1ubuntu1.26 [292 kB]
Get:86 http://archive.ubuntu.com/ubuntu jammy/main amd64 libjsoncpp25 amd64 1.9.5-3 [80.0 kB]
Get:87 http://archive.ubuntu.com/ubuntu jammy/main amd64 librhash0 amd64 1.4.2-1ubuntu1 [125 kB]
Get:88 http://archive.ubuntu.com/ubuntu jammy/main amd64 dh-elpa-helper all 2.0.9ubuntu1 [7610 B]
Get:89 http://archive.ubuntu.com/ubuntu jammy/main amd64 emacsen-common all 3.0.4 [14.9 kB]
Get:90 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 cmake-data all 3.22.1-1ubuntu1.22.04.2 [1913 kB]
Get:91 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 cmake amd64 3.22.1-1ubuntu1.22.04.2 [5010 kB]
Get:92 http://archive.ubuntu.com/ubuntu jammy/main amd64 mysql-common all 5.8+1.0.8 [7212 B]
Get:93 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libmysqlclient21 amd64 8.0.46-0ubuntu0.22.04.3 [1336 kB]
Get:94 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libssl-dev amd64 3.0.2-0ubuntu1.26 [2377 kB]
Get:95 http://archive.ubuntu.com/ubuntu jammy/main amd64 libzstd-dev amd64 1.4.8+dfsg-3build1 [401 kB]
Get:96 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 zlib1g-dev amd64 1:1.2.11.dfsg-2ubuntu9.2 [164 kB]
Get:97 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libmysqlclient-dev amd64 8.0.46-0ubuntu0.22.04.3 [1705 kB]
Get:98 http://archive.ubuntu.com/ubuntu jammy/main amd64 default-libmysqlclient-dev amd64 1.0.8 [3586 B]
Get:99 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libllvm14 amd64 1:14.0.0-1ubuntu1.1 [24.0 MB]
Get:100 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 libclang-cpp14 amd64 1:14.0.0-1ubuntu1.1 [12.1 MB]
Get:101 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 libclang1-14 amd64 1:14.0.0-1ubuntu1.1 [6792 kB]
Get:102 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libxapian30 amd64 1.4.18-4 [701 kB]
Get:103 http://archive.ubuntu.com/ubuntu jammy/universe amd64 doxygen amd64 1.9.1-2ubuntu2 [4620 kB]
Get:104 http://archive.ubuntu.com/ubuntu jammy/universe amd64 fonts-lyx all 2.3.6-1 [159 kB]
Get:105 http://archive.ubuntu.com/ubuntu jammy/universe amd64 gdal-data all 3.4.1+dfsg-1build4 [216 kB]
Get:106 http://archive.ubuntu.com/ubuntu jammy/universe amd64 aglfn all 1.7+git20191031.4036a9c-2 [30.6 kB]
Get:107 http://archive.ubuntu.com/ubuntu jammy/universe amd64 gnuplot-data all 5.4.2+dfsg2-2 [75.3 kB]
Get:108 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libtiff5 amd64 4.3.0-6ubuntu0.13 [185 kB]
Get:109 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libxpm4 amd64 1:3.5.12-1ubuntu0.22.04.3 [36.5 kB]
Get:110 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libgd3 amd64 2.3.0-2ubuntu2.3 [129 kB]
Get:111 http://archive.ubuntu.com/ubuntu jammy/universe amd64 liblua5.4-0 amd64 5.4.4-1 [152 kB]
Get:112 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 libqt5printsupport5 amd64 5.15.3+dfsg-2ubuntu0.2 [214 kB]
Get:113 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libwxbase3.0-0v5 amd64 3.0.5.1+dfsg-4 [881 kB]
Get:114 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libnotify4 amd64 0.7.9-3ubuntu5.22.04.1 [20.3 kB]
Get:115 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libwxgtk3.0-gtk3-0v5 amd64 3.0.5.1+dfsg-4 [4368 kB]
Get:116 http://archive.ubuntu.com/ubuntu jammy/universe amd64 gnuplot-qt amd64 5.4.2+dfsg2-2 [1156 kB]
Get:117 http://archive.ubuntu.com/ubuntu jammy/universe amd64 gnuplot all 5.4.2+dfsg2-2 [3576 B]
Get:118 http://archive.ubuntu.com/ubuntu jammy/universe amd64 googletest all 1.11.0-3 [541 kB]
Get:119 http://archive.ubuntu.com/ubuntu jammy/universe amd64 hdf5-helpers amd64 1.10.7+repack-4ubuntu2 [14.2 kB]
Get:120 http://archive.ubuntu.com/ubuntu jammy/main amd64 icu-devtools amd64 70.1-2 [197 kB]
Get:121 http://archive.ubuntu.com/ubuntu jammy/main amd64 libjson-perl all 4.04000-1 [81.8 kB]
Get:122 http://archive.ubuntu.com/ubuntu jammy/main amd64 libperlio-gzip-perl amd64 0.19-1build8 [14.9 kB]
Get:123 http://archive.ubuntu.com/ubuntu jammy/universe amd64 lcov all 1.15-1 [99.5 kB]
Get:124 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libaec0 amd64 1.0.6-1 [20.1 kB]
Get:125 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 libaom3 amd64 3.3.0-1ubuntu0.1 [1748 kB]
Get:126 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 libaom-dev amd64 3.3.0-1ubuntu0.1 [2093 kB]
Get:127 http://archive.ubuntu.com/ubuntu jammy/main amd64 libblas3 amd64 3.10.0-2ubuntu1 [228 kB]
Get:128 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libgfortran5 amd64 12.3.0-1ubuntu1~22.04.3 [879 kB]
Get:129 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libopenblas0-pthread amd64 0.3.20+ds-1 [6803 kB]
Get:130 http://archive.ubuntu.com/ubuntu jammy/main amd64 liblapack3 amd64 3.10.0-2ubuntu1 [2504 kB]
Get:131 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libarpack2 amd64 3.8.0-1 [92.4 kB]
Get:132 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libsuperlu5 amd64 5.3.0+dfsg1-2 [183 kB]
Get:133 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libarmadillo10 amd64 1:10.8.2+dfsg-1 [105 kB]
Get:134 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libopenblas-pthread-dev amd64 0.3.20+ds-1 [4634 kB]
Get:135 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libarpack2-dev amd64 3.8.0-1 [105 kB]
Get:136 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libsz2 amd64 1.0.6-1 [5354 B]
Get:137 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libhdf5-103-1 amd64 1.10.7+repack-4ubuntu2 [1295 kB]
Get:138 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libhdf5-fortran-102 amd64 1.10.7+repack-4ubuntu2 [90.9 kB]
Get:139 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libhdf5-hl-100 amd64 1.10.7+repack-4ubuntu2 [59.1 kB]
Get:140 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libhdf5-hl-fortran-100 amd64 1.10.7+repack-4ubuntu2 [33.8 kB]
Get:141 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libhdf5-cpp-103-1 amd64 1.10.7+repack-4ubuntu2 [129 kB]
Get:142 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libhdf5-hl-cpp-100 amd64 1.10.7+repack-4ubuntu2 [10.6 kB]
Get:143 http://archive.ubuntu.com/ubuntu jammy/main amd64 libjpeg-turbo8-dev amd64 2.1.2-0ubuntu1 [257 kB]
Get:144 http://archive.ubuntu.com/ubuntu jammy/main amd64 libjpeg8-dev amd64 8c-2ubuntu10 [1476 B]
Get:145 http://archive.ubuntu.com/ubuntu jammy/main amd64 libjpeg-dev amd64 8c-2ubuntu10 [1472 B]
Get:146 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libaec-dev amd64 1.0.6-1 [17.9 kB]
Get:147 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libcurl4-openssl-dev amd64 7.81.0-1ubuntu1.26 [387 kB]
Get:148 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libhdf5-dev amd64 1.10.7+repack-4ubuntu2 [2684 kB]
Get:149 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libopenblas0 amd64 0.3.20+ds-1 [6098 B]
Get:150 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libopenblas-dev amd64 0.3.20+ds-1 [18.6 kB]
Get:151 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libsuperlu-dev amd64 5.3.0+dfsg1-2 [20.0 kB]
Get:152 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libarmadillo-dev amd64 1:10.8.2+dfsg-1 [399 kB]
Get:153 http://archive.ubuntu.com/ubuntu jammy/main amd64 libsnappy1v5 amd64 1.1.8-1build3 [17.5 kB]
Get:154 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libblosc1 amd64 1.21.1+ds2-2 [35.8 kB]
Get:155 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libblosc-dev amd64 1.21.1+ds2-2 [44.1 kB]
Get:156 http://archive.ubuntu.com/ubuntu jammy/main amd64 libboost1.74-dev amd64 1.74.0-14ubuntu3 [9609 kB]
Get:157 http://archive.ubuntu.com/ubuntu jammy/main amd64 libboost-dev amd64 1.74.0.3ubuntu7 [3490 B]
Get:158 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libcfitsio9 amd64 4.0.0-1 [519 kB]
Get:159 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libcfitsio-dev amd64 4.0.0-1 [591 kB]
Get:160 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libcharls2 amd64 2.3.4-1 [87.0 kB]
Get:161 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libcharls-dev amd64 2.3.4-1 [22.4 kB]
Get:162 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libdav1d5 amd64 0.9.2-1 [463 kB]
Get:163 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libdav1d-dev amd64 0.9.2-1 [24.1 kB]
Get:164 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 libde265-0 amd64 1.0.8-1ubuntu0.3 [290 kB]
Get:165 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 libde265-dev amd64 1.0.8-1ubuntu0.3 [12.3 kB]
Get:166 http://archive.ubuntu.com/ubuntu jammy/main amd64 libdeflate-dev amd64 1.10-2 [59.2 kB]
Get:167 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libexpat1-dev amd64 2.4.7-1ubuntu0.7 [148 kB]
Get:168 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libfyba0 amd64 4.1.1-7 [113 kB]
Get:169 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libfyba-dev amd64 4.1.1-7 [166 kB]
Get:170 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libfreexl1 amd64 1.0.6-1 [33.5 kB]
Get:171 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libgeos3.10.2 amd64 3.10.2-1 [713 kB]
Get:172 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libgeos-c1v5 amd64 3.10.2-1 [82.5 kB]
Get:173 http://archive.ubuntu.com/ubuntu jammy/universe amd64 proj-data all 8.2.1-1 [10.0 MB]
Get:174 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libproj22 amd64 8.2.1-1 [1257 kB]
Get:175 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libgeotiff5 amd64 1.7.0-2build1 [67.1 kB]
Get:176 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libgif7 amd64 5.1.9-2ubuntu0.3 [34.3 kB]
Get:177 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libhdf4-0-alt amd64 4.2.15-4 [290 kB]
Get:178 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libx265-199 amd64 3.5-2 [1170 kB]
Get:179 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libheif1 amd64 1.12.0-2build1 [196 kB]
Get:180 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libminizip1 amd64 1.1-8build1 [20.2 kB]
Get:181 http://archive.ubuntu.com/ubuntu jammy/universe amd64 liburiparser1 amd64 0.9.6+dfsg-1 [36.4 kB]
Get:182 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libkmlbase1 amd64 1.3.0-9 [45.0 kB]
Get:183 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libkmldom1 amd64 1.3.0-9 [150 kB]
Get:184 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libkmlengine1 amd64 1.3.0-9 [71.7 kB]
Get:185 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libnetcdf19 amd64 1:4.8.1-1 [456 kB]
Get:186 http://archive.ubuntu.com/ubuntu jammy/main amd64 libltdl7 amd64 2.4.6-15build2 [39.6 kB]
Get:187 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libodbc2 amd64 2.3.9-5ubuntu0.1 [159 kB]
Get:188 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 unixodbc-common all 2.3.9-5ubuntu0.1 [9256 B]
Get:189 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libodbcinst2 amd64 2.3.9-5ubuntu0.1 [31.9 kB]
Get:190 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libogdi4.1 amd64 4.1.0+ds-5 [197 kB]
Get:191 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libopenjp2-7 amd64 2.4.0-6ubuntu0.5 [158 kB]
Get:192 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libnspr4 amd64 2:4.35-0ubuntu0.22.04.1 [119 kB]
Get:193 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libnss3 amd64 2:3.98-0ubuntu0.22.04.4 [1347 kB]
Get:194 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libpoppler118 amd64 22.02.0-2ubuntu0.13 [1081 kB]
Get:195 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libpq5 amd64 14.24-0ubuntu0.22.04.1 [157 kB]
Get:196 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libqhull-r8.0 amd64 2020.2-4 [196 kB]
Get:197 http://archive.ubuntu.com/ubuntu jammy/universe amd64 librttopo1 amd64 1.1.0-2 [178 kB]
Get:198 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libspatialite7 amd64 5.0.1-2build2 [2092 kB]
Get:199 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 libxerces-c3.2 amd64 3.2.3+debian-3ubuntu0.1 [929 kB]
Get:200 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libgdal30 amd64 3.4.1+dfsg-1build4 [7642 kB]
Get:201 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libgeos-dev amd64 3.10.2-1 [46.6 kB]
Get:202 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libgif-dev amd64 5.1.9-2ubuntu0.3 [22.5 kB]
Get:203 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libgtest-dev amd64 1.11.0-3 [250 kB]
Get:204 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libx265-dev amd64 3.5-2 [1374 kB]
Get:205 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libheif-dev amd64 1.12.0-2build1 [26.4 kB]
Get:206 http://archive.ubuntu.com/ubuntu jammy/main amd64 libicu-dev amd64 70.1-2 [11.6 MB]
Get:207 http://archive.ubuntu.com/ubuntu jammy/main amd64 libimagequant0 amd64 2.17.0-1 [34.6 kB]
Get:208 http://archive.ubuntu.com/ubuntu jammy/main amd64 libjs-jquery all 3.6.0+dfsg+~3.5.13-1 [321 kB]
Get:209 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libjs-jquery-ui all 1.13.1+dfsg-1 [253 kB]
Get:210 http://archive.ubuntu.com/ubuntu jammy/main amd64 libjs-underscore all 1.13.2~dfsg-2 [118 kB]
Get:211 http://archive.ubuntu.com/ubuntu jammy/main amd64 libjs-sphinxdoc all 4.3.2-1 [139 kB]
Get:212 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libkmlconvenience1 amd64 1.3.0-9 [45.1 kB]
Get:213 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libkmlregionator1 amd64 1.3.0-9 [19.9 kB]
Get:214 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libkmlxsd1 amd64 1.3.0-9 [27.3 kB]
Get:215 http://archive.ubuntu.com/ubuntu jammy/universe amd64 liblbfgsb0 amd64 3.0+dfsg.3-10 [29.9 kB]
Get:216 http://archive.ubuntu.com/ubuntu jammy/main amd64 libltdl-dev amd64 2.4.6-15build2 [169 kB]
Get:217 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libminizip-dev amd64 1.1-8build1 [26.7 kB]
Get:218 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libnetcdf-dev amd64 1:4.8.1-1 [50.3 kB]
Get:219 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libodbccr2 amd64 2.3.9-5ubuntu0.1 [16.7 kB]
Get:220 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libogdi-dev amd64 4.1.0+ds-5 [22.1 kB]
Get:221 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libpcre2-32-0 amd64 10.39-3ubuntu0.1 [194 kB]
Get:222 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libpcre2-posix3 amd64 10.39-3ubuntu0.1 [6130 B]
Get:223 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libpcre2-dev amd64 10.39-3ubuntu0.1 [730 kB]
Get:224 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libpng-dev amd64 1.6.37-3ubuntu0.6 [193 kB]
Get:225 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libpoppler-dev amd64 22.02.0-2ubuntu0.13 [5186 B]
Get:226 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libpoppler-private-dev amd64 22.02.0-2ubuntu0.13 [198 kB]
Get:227 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libpq-dev amd64 14.24-0ubuntu0.22.04.1 [149 kB]
Get:228 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libpython3.10-dev amd64 3.10.12-1~22.04.16 [4766 kB]
Get:229 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libpython3-dev amd64 3.10.6-1~22.04.1 [7064 B]
Get:230 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libqhull8.0 amd64 2020.2-4 [193 kB]
Get:231 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libqhullcpp8.0 amd64 2020.2-4 [53.0 kB]
Get:232 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libqhull-dev amd64 2020.2-4 [502 kB]
Get:233 http://archive.ubuntu.com/ubuntu jammy/main amd64 libraqm0 amd64 0.7.0-4ubuntu1 [11.7 kB]
Get:234 http://archive.ubuntu.com/ubuntu jammy/universe amd64 librttopo-dev amd64 1.1.0-2 [220 kB]
Get:235 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libsqlite3-dev amd64 3.37.2-2ubuntu0.7 [847 kB]
Get:236 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libtbbmalloc2 amd64 2021.5.0-7ubuntu2 [49.6 kB]
Get:237 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libtbb12 amd64 2021.5.0-7ubuntu2 [84.8 kB]
Get:238 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libjbig-dev amd64 2.1-3.1ubuntu0.22.04.1 [27.4 kB]
Get:239 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 liblzma-dev amd64 5.2.5-2ubuntu1.1 [159 kB]
Get:240 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libtiffxx5 amd64 4.3.0-6ubuntu0.13 [5742 B]
Get:241 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libtiff-dev amd64 4.3.0-6ubuntu0.13 [316 kB]
Get:242 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libtinyxml2-9 amd64 9.0.0+dfsg-3 [32.5 kB]
Get:243 http://archive.ubuntu.com/ubuntu jammy/universe amd64 liburiparser-dev amd64 0.9.6+dfsg-1 [12.2 kB]
Get:244 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libwebpdemux2 amd64 1.2.2-2ubuntu0.22.04.2 [9964 B]
Get:245 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libwebpmux3 amd64 1.2.2-2ubuntu0.22.04.2 [20.5 kB]
Get:246 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 libxerces-c-dev amd64 3.2.3+debian-3ubuntu0.1 [1820 kB]
Get:247 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libxml2-dev amd64 2.9.13+dfsg-1ubuntu0.12 [805 kB]
Get:248 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libxsimd-dev amd64 7.6.0-2 [108 kB]
Get:249 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libxslt1.1 amd64 1.1.34-4ubuntu0.22.04.5 [165 kB]
Get:250 http://archive.ubuntu.com/ubuntu jammy/universe amd64 nlohmann-json3-dev all 3.10.5-2 [167 kB]
Get:251 http://archive.ubuntu.com/ubuntu jammy/main amd64 pkg-config amd64 0.29.2-1ubuntu3 [48.2 kB]
Get:252 http://archive.ubuntu.com/ubuntu jammy/universe amd64 python-matplotlib-data all 3.5.1-2build1 [2942 kB]
Get:253 http://archive.ubuntu.com/ubuntu jammy/main amd64 python3-appdirs all 1.4.4-2 [11.4 kB]
Get:254 http://archive.ubuntu.com/ubuntu jammy/universe amd64 python3-gast all 0.5.2-2 [9394 B]
Get:255 http://archive.ubuntu.com/ubuntu jammy/universe amd64 python3-beniget all 0.4.1-2 [9904 B]
Get:256 http://archive.ubuntu.com/ubuntu jammy/universe amd64 python3-brotli amd64 1.0.9-2build6 [319 kB]
Get:257 http://archive.ubuntu.com/ubuntu jammy/universe amd64 python3-cycler all 0.11.0-1 [8156 B]
Get:258 http://archive.ubuntu.com/ubuntu jammy/main amd64 python3-dateutil all 2.8.1-6 [78.4 kB]
Get:259 http://archive.ubuntu.com/ubuntu jammy/main amd64 python3-decorator all 4.4.2-0ubuntu1 [10.3 kB]
Get:260 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 python3.10-dev amd64 3.10.12-1~22.04.16 [508 kB]
Get:261 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 python3-dev amd64 3.10.6-1~22.04.1 [26.0 kB]
Get:262 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 python3-numpy amd64 1:1.21.5-1ubuntu22.04.1 [3467 kB]
Get:263 http://archive.ubuntu.com/ubuntu jammy/main amd64 python3-ply all 3.11-5 [47.5 kB]
Get:264 http://archive.ubuntu.com/ubuntu jammy/universe amd64 python3-pythran amd64 0.10.0+ds2-1 [423 kB]
Get:265 http://archive.ubuntu.com/ubuntu jammy/universe amd64 python3-scipy amd64 1.8.0-1exp2ubuntu1 [14.7 MB]
Get:266 http://archive.ubuntu.com/ubuntu jammy/universe amd64 python3-ufolib2 all 0.13.1+dfsg1-1 [32.2 kB]
Get:267 http://archive.ubuntu.com/ubuntu jammy/universe amd64 python3-mpmath all 1.2.1-2 [419 kB]
Get:268 http://archive.ubuntu.com/ubuntu jammy/universe amd64 python3-sympy all 1.9-1 [4312 kB]
Get:269 http://archive.ubuntu.com/ubuntu jammy/universe amd64 python3-fs all 2.4.12-1 [84.9 kB]
Get:270 http://archive.ubuntu.com/ubuntu jammy/main amd64 python3-lxml amd64 4.8.0-1build1 [1150 kB]
Get:271 http://archive.ubuntu.com/ubuntu jammy/universe amd64 python3-lz4 amd64 3.1.3+dfsg-1build3 [33.3 kB]
Get:272 http://archive.ubuntu.com/ubuntu jammy/universe amd64 python3-unicodedata2 amd64 14.0.0+ds-8 [376 kB]
Get:273 http://archive.ubuntu.com/ubuntu jammy/universe amd64 unicode-data all 14.0.0-1.1 [8206 kB]
Get:274 http://archive.ubuntu.com/ubuntu jammy/universe amd64 python3-fonttools amd64 4.29.1-2build1 [810 kB]
Get:275 http://archive.ubuntu.com/ubuntu jammy/universe amd64 python3-kiwisolver amd64 1.3.2-1build1 [48.0 kB]
Get:276 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 python3-pil amd64 9.0.1-1ubuntu0.4 [420 kB]
Get:277 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 python3-tk amd64 3.10.8-1~22.04 [110 kB]
Get:278 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 python3-pil.imagetk amd64 9.0.1-1ubuntu0.4 [9622 B]
Get:279 http://archive.ubuntu.com/ubuntu jammy/main amd64 python3-packaging all 21.3-1 [30.7 kB]
Get:280 http://archive.ubuntu.com/ubuntu jammy/universe amd64 python3-matplotlib amd64 3.5.1-2build1 [5937 kB]
Get:281 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 python3-wheel all 0.37.1-2ubuntu0.22.04.1 [32.0 kB]
Get:282 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 python3-pip all 22.0.2+dfsg-1ubuntu0.7 [1306 kB]
Get:283 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 python3-pip-whl all 22.0.2+dfsg-1ubuntu0.7 [1683 kB]
Get:284 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 python3-setuptools-whl all 59.6.0-1.2ubuntu0.22.04.3 [789 kB]
Get:285 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 python3.10-venv amd64 3.10.12-1~22.04.16 [5724 B]
Get:286 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 python3-venv amd64 3.10.6-1~22.04.1 [1042 B]
Get:287 http://archive.ubuntu.com/ubuntu jammy/universe amd64 swig4.0 amd64 4.0.2-1ubuntu1 [1110 kB]
Get:288 http://archive.ubuntu.com/ubuntu jammy/universe amd64 swig all 4.0.2-1ubuntu1 [5632 B]
Get:289 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libeigen3-dev all 3.4.0-2ubuntu2 [1056 kB]
Get:290 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libfreexl-dev amd64 1.0.6-1 [31.4 kB]
Get:291 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libproj-dev amd64 8.2.1-1 [1594 kB]
Get:292 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libgeotiff-dev amd64 1.7.0-2build1 [92.4 kB]
Get:293 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libhdf4-alt-dev amd64 4.2.15-4 [406 kB]
Get:294 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libjson-c-dev amd64 0.15-3~ubuntu1.22.04.2 [60.5 kB]
Get:295 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libkml-dev amd64 1.3.0-9 [933 kB]
Get:296 http://archive.ubuntu.com/ubuntu jammy/main amd64 liblz4-dev amd64 1.9.3-2build2 [80.7 kB]
Get:297 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libopenjp2-7-dev amd64 2.4.0-6ubuntu0.5 [245 kB]
Get:298 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libspatialite-dev amd64 5.0.1-2build2 [2397 kB]
Get:299 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libwebp-dev amd64 1.2.2-2ubuntu0.22.04.2 [298 kB]
Get:300 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 unixodbc-dev amd64 2.3.9-5ubuntu0.1 [248 kB]
Get:301 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libgdal-dev amd64 3.4.1+dfsg-1build4 [10.6 MB]
Get:302 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libtbb-dev amd64 2021.5.0-7ubuntu2 [191 kB]
Get:303 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libtinyxml2-dev amd64 9.0.0+dfsg-3 [18.6 kB]
Preconfiguring packages ...
Fetched 318 MB in 1min 28s (3624 kB/s)
(Reading database ... 
(Reading database ... 5%
(Reading database ... 10%
(Reading database ... 15%
(Reading database ... 20%
(Reading database ... 25%
(Reading database ... 30%
(Reading database ... 35%
(Reading database ... 40%
(Reading database ... 45%
(Reading database ... 50%
(Reading database ... 55%
(Reading database ... 60%
(Reading database ... 65%
(Reading database ... 70%
(Reading database ... 75%
(Reading database ... 80%
(Reading database ... 85%
(Reading database ... 90%
(Reading database ... 95%
(Reading database ... 100%
(Reading database ... 42622 files and directories currently installed.)
Preparing to unpack .../libc6_2.35-0ubuntu3.14_amd64.deb ...
Unpacking libc6:amd64 (2.35-0ubuntu3.14) over (2.35-0ubuntu3.13) ...
Setting up libc6:amd64 (2.35-0ubuntu3.14) ...
(Reading database ... 
(Reading database ... 5%
(Reading database ... 10%
(Reading database ... 15%
(Reading database ... 20%
(Reading database ... 25%
(Reading database ... 30%
(Reading database ... 35%
(Reading database ... 40%
(Reading database ... 45%
(Reading database ... 50%
(Reading database ... 55%
(Reading database ... 60%
(Reading database ... 65%
(Reading database ... 70%
(Reading database ... 75%
(Reading database ... 80%
(Reading database ... 85%
(Reading database ... 90%
(Reading database ... 95%
(Reading database ... 100%
(Reading database ... 42622 files and directories currently installed.)
Preparing to unpack .../libpython3.10_3.10.12-1~22.04.16_amd64.deb ...
Unpacking libpython3.10:amd64 (3.10.12-1~22.04.16) over (3.10.12-1~22.04.15) ...
Preparing to unpack .../libssl3_3.0.2-0ubuntu1.26_amd64.deb ...
Unpacking libssl3:amd64 (3.0.2-0ubuntu1.26) over (3.0.2-0ubuntu1.21) ...
Setting up libssl3:amd64 (3.0.2-0ubuntu1.26) ...
(Reading database ... 
(Reading database ... 5%
(Reading database ... 10%
(Reading database ... 15%
(Reading database ... 20%
(Reading database ... 25%
(Reading database ... 30%
(Reading database ... 35%
(Reading database ... 40%
(Reading database ... 45%
(Reading database ... 50%
(Reading database ... 55%
(Reading database ... 60%
(Reading database ... 65%
(Reading database ... 70%
(Reading database ... 75%
(Reading database ... 80%
(Reading database ... 85%
(Reading database ... 90%
(Reading database ... 95%
(Reading database ... 100%
(Reading database ... 42622 files and directories currently installed.)
Preparing to unpack .../python3.10_3.10.12-1~22.04.16_amd64.deb ...
Unpacking python3.10 (3.10.12-1~22.04.16) over (3.10.12-1~22.04.15) ...
Preparing to unpack .../libpython3.10-stdlib_3.10.12-1~22.04.16_amd64.deb ...
Unpacking libpython3.10-stdlib:amd64 (3.10.12-1~22.04.16) over (3.10.12-1~22.04.15) ...
Preparing to unpack .../python3.10-minimal_3.10.12-1~22.04.16_amd64.deb ...
Unpacking python3.10-minimal (3.10.12-1~22.04.16) over (3.10.12-1~22.04.15) ...
Preparing to unpack .../libpython3.10-minimal_3.10.12-1~22.04.16_amd64.deb ...
Unpacking libpython3.10-minimal:amd64 (3.10.12-1~22.04.16) over (3.10.12-1~22.04.15) ...
Preparing to unpack .../liblzma5_5.2.5-2ubuntu1.1_amd64.deb ...
Unpacking liblzma5:amd64 (5.2.5-2ubuntu1.1) over (5.2.5-2ubuntu1) ...
Setting up liblzma5:amd64 (5.2.5-2ubuntu1.1) ...
(Reading database ... 
(Reading database ... 5%
(Reading database ... 10%
(Reading database ... 15%
(Reading database ... 20%
(Reading database ... 25%
(Reading database ... 30%
(Reading database ... 35%
(Reading database ... 40%
(Reading database ... 45%
(Reading database ... 50%
(Reading database ... 55%
(Reading database ... 60%
(Reading database ... 65%
(Reading database ... 70%
(Reading database ... 75%
(Reading database ... 80%
(Reading database ... 85%
(Reading database ... 90%
(Reading database ... 95%
(Reading database ... 100%
(Reading database ... 42622 files and directories currently installed.)
Preparing to unpack .../000-libsqlite3-0_3.37.2-2ubuntu0.7_amd64.deb ...
Unpacking libsqlite3-0:amd64 (3.37.2-2ubuntu0.7) over (3.37.2-2ubuntu0.5) ...
Selecting previously unselected package libdouble-conversion3:amd64.
Preparing to unpack .../001-libdouble-conversion3_3.1.7-4_amd64.deb ...
Unpacking libdouble-conversion3:amd64 (3.1.7-4) ...
Selecting previously unselected package libpcre2-16-0:amd64.
Preparing to unpack .../002-libpcre2-16-0_10.39-3ubuntu0.1_amd64.deb ...
Unpacking libpcre2-16-0:amd64 (10.39-3ubuntu0.1) ...
Selecting previously unselected package libqt5core5a:amd64.
Preparing to unpack .../003-libqt5core5a_5.15.3+dfsg-2ubuntu0.2_amd64.deb ...
Unpacking libqt5core5a:amd64 (5.15.3+dfsg-2ubuntu0.2) ...
Selecting previously unselected package libice6:amd64.
Preparing to unpack .../004-libice6_2%3a1.0.10-1build2_amd64.deb ...
Unpacking libice6:amd64 (2:1.0.10-1build2) ...
Selecting previously unselected package libevdev2:amd64.
Preparing to unpack .../005-libevdev2_1.12.1+dfsg-1_amd64.deb ...
Unpacking libevdev2:amd64 (1.12.1+dfsg-1) ...
Selecting previously unselected package libmtdev1:amd64.
Preparing to unpack .../006-libmtdev1_1.1.6-1build4_amd64.deb ...
Unpacking libmtdev1:amd64 (1.1.6-1build4) ...
Selecting previously unselected package libgudev-1.0-0:amd64.
Preparing to unpack .../007-libgudev-1.0-0_1%3a237-2build1_amd64.deb ...
Unpacking libgudev-1.0-0:amd64 (1:237-2build1) ...
Selecting previously unselected package libwacom-common.
Preparing to unpack .../008-libwacom-common_2.2.0-1_all.deb ...
Unpacking libwacom-common (2.2.0-1) ...
Selecting previously unselected package libwacom9:amd64.
Preparing to unpack .../009-libwacom9_2.2.0-1_amd64.deb ...
Unpacking libwacom9:amd64 (2.2.0-1) ...
Selecting previously unselected package libinput-bin.
Preparing to unpack .../010-libinput-bin_1.20.0-1ubuntu0.4_amd64.deb ...
Unpacking libinput-bin (1.20.0-1ubuntu0.4) ...
Selecting previously unselected package libinput10:amd64.
Preparing to unpack .../011-libinput10_1.20.0-1ubuntu0.4_amd64.deb ...
Unpacking libinput10:amd64 (1.20.0-1ubuntu0.4) ...
Selecting previously unselected package libmd4c0:amd64.
Preparing to unpack .../012-libmd4c0_0.4.8-1_amd64.deb ...
Unpacking libmd4c0:amd64 (0.4.8-1) ...
Preparing to unpack .../013-libpng16-16_1.6.37-3ubuntu0.6_amd64.deb ...
Unpacking libpng16-16:amd64 (1.6.37-3ubuntu0.6) over (1.6.37-3ubuntu0.4) ...
Selecting previously unselected package libqt5dbus5:amd64.
Preparing to unpack .../014-libqt5dbus5_5.15.3+dfsg-2ubuntu0.2_amd64.deb ...
Unpacking libqt5dbus5:amd64 (5.15.3+dfsg-2ubuntu0.2) ...
Selecting previously unselected package libqt5network5:amd64.
Preparing to unpack .../015-libqt5network5_5.15.3+dfsg-2ubuntu0.2_amd64.deb ...
Unpacking libqt5network5:amd64 (5.15.3+dfsg-2ubuntu0.2) ...
Selecting previously unselected package libsm6:amd64.
Preparing to unpack .../016-libsm6_2%3a1.2.3-1build2_amd64.deb ...
Unpacking libsm6:amd64 (2:1.2.3-1build2) ...
Selecting previously unselected package libxcb-icccm4:amd64.
Preparing to unpack .../017-libxcb-icccm4_0.4.1-1.1build2_amd64.deb ...
Unpacking libxcb-icccm4:amd64 (0.4.1-1.1build2) ...
Selecting previously unselected package libxcb-util1:amd64.
Preparing to unpack .../018-libxcb-util1_0.4.0-1build2_amd64.deb ...
Unpacking libxcb-util1:amd64 (0.4.0-1build2) ...
Selecting previously unselected package libxcb-image0:amd64.
Preparing to unpack .../019-libxcb-image0_0.4.0-2_amd64.deb ...
Unpacking libxcb-image0:amd64 (0.4.0-2) ...
Selecting previously unselected package libxcb-keysyms1:amd64.
Preparing to unpack .../020-libxcb-keysyms1_0.4.0-1build3_amd64.deb ...
Unpacking libxcb-keysyms1:amd64 (0.4.0-1build3) ...
Selecting previously unselected package libxcb-render-util0:amd64.
Preparing to unpack .../021-libxcb-render-util0_0.3.9-1build3_amd64.deb ...
Unpacking libxcb-render-util0:amd64 (0.3.9-1build3) ...
Selecting previously unselected package libxcb-shape0:amd64.
Preparing to unpack .../022-libxcb-shape0_1.14-3ubuntu3_amd64.deb ...
Unpacking libxcb-shape0:amd64 (1.14-3ubuntu3) ...
Selecting previously unselected package libxcb-xinerama0:amd64.
Preparing to unpack .../023-libxcb-xinerama0_1.14-3ubuntu3_amd64.deb ...
Unpacking libxcb-xinerama0:amd64 (1.14-3ubuntu3) ...
Selecting previously unselected package libxcb-xinput0:amd64.
Preparing to unpack .../024-libxcb-xinput0_1.14-3ubuntu3_amd64.deb ...
Unpacking libxcb-xinput0:amd64 (1.14-3ubuntu3) ...
Selecting previously unselected package libxcb-xkb1:amd64.
Preparing to unpack .../025-libxcb-xkb1_1.14-3ubuntu3_amd64.deb ...
Unpacking libxcb-xkb1:amd64 (1.14-3ubuntu3) ...
Selecting previously unselected package libxkbcommon-x11-0:amd64.
Preparing to unpack .../026-libxkbcommon-x11-0_1.4.0-1_amd64.deb ...
Unpacking libxkbcommon-x11-0:amd64 (1.4.0-1) ...
Selecting previously unselected package libqt5gui5:amd64.
Preparing to unpack .../027-libqt5gui5_5.15.3+dfsg-2ubuntu0.2_amd64.deb ...
Unpacking libqt5gui5:amd64 (5.15.3+dfsg-2ubuntu0.2) ...
Selecting previously unselected package libqt5widgets5:amd64.
Preparing to unpack .../028-libqt5widgets5_5.15.3+dfsg-2ubuntu0.2_amd64.deb ...
Unpacking libqt5widgets5:amd64 (5.15.3+dfsg-2ubuntu0.2) ...
Selecting previously unselected package libqt5svg5:amd64.
Preparing to unpack .../029-libqt5svg5_5.15.3-1_amd64.deb ...
Unpacking libqt5svg5:amd64 (5.15.3-1) ...
Preparing to unpack .../030-libxml2_2.9.13+dfsg-1ubuntu0.12_amd64.deb ...
Unpacking libxml2:amd64 (2.9.13+dfsg-1ubuntu0.12) over (2.9.13+dfsg-1ubuntu0.11) ...
Selecting previously unselected package m4.
Preparing to unpack .../031-m4_1.4.18-5ubuntu2_amd64.deb ...
Unpacking m4 (1.4.18-5ubuntu2) ...
Selecting previously unselected package autoconf.
Preparing to unpack .../032-autoconf_2.71-2_all.deb ...
Unpacking autoconf (2.71-2) ...
Selecting previously unselected package autotools-dev.
Preparing to unpack .../033-autotools-dev_20220109.1_all.deb ...
Unpacking autotools-dev (20220109.1) ...
Selecting previously unselected package automake.
Preparing to unpack .../034-automake_1%3a1.16.5-1.3_all.deb ...
Unpacking automake (1:1.16.5-1.3) ...
Selecting previously unselected package libtcl8.6:amd64.
Preparing to unpack .../035-libtcl8.6_8.6.12+dfsg-1build1_amd64.deb ...
Unpacking libtcl8.6:amd64 (8.6.12+dfsg-1build1) ...
Selecting previously unselected package libxft2:amd64.
Preparing to unpack .../036-libxft2_2.3.4-1_amd64.deb ...
Unpacking libxft2:amd64 (2.3.4-1) ...
Selecting previously unselected package libxss1:amd64.
Preparing to unpack .../037-libxss1_1%3a1.2.3-1build2_amd64.deb ...
Unpacking libxss1:amd64 (1:1.2.3-1build2) ...
Selecting previously unselected package libtk8.6:amd64.
Preparing to unpack .../038-libtk8.6_8.6.12-1build1_amd64.deb ...
Unpacking libtk8.6:amd64 (8.6.12-1build1) ...
Selecting previously unselected package tk8.6-blt2.5.
Preparing to unpack .../039-tk8.6-blt2.5_2.5.3+dfsg-4.1build2_amd64.deb ...
Unpacking tk8.6-blt2.5 (2.5.3+dfsg-4.1build2) ...
Selecting previously unselected package blt.
Preparing to unpack .../040-blt_2.5.3+dfsg-4.1build2_amd64.deb ...
Unpacking blt (2.5.3+dfsg-4.1build2) ...
Selecting previously unselected package libc-dev-bin.
Preparing to unpack .../041-libc-dev-bin_2.35-0ubuntu3.14_amd64.deb ...
Unpacking libc-dev-bin (2.35-0ubuntu3.14) ...
Selecting previously unselected package linux-libc-dev:amd64.
Preparing to unpack .../042-linux-libc-dev_5.15.0-190.200_amd64.deb ...
Unpacking linux-libc-dev:amd64 (5.15.0-190.200) ...
Selecting previously unselected package libcrypt-dev:amd64.
Preparing to unpack .../043-libcrypt-dev_1%3a4.4.27-1_amd64.deb ...
Unpacking libcrypt-dev:amd64 (1:4.4.27-1) ...
Selecting previously unselected package rpcsvc-proto.
Preparing to unpack .../044-rpcsvc-proto_1.4.2-0ubuntu6_amd64.deb ...
Unpacking rpcsvc-proto (1.4.2-0ubuntu6) ...
Selecting previously unselected package libtirpc-dev:amd64.
Preparing to unpack .../045-libtirpc-dev_1.3.2-2ubuntu0.1_amd64.deb ...
Unpacking libtirpc-dev:amd64 (1.3.2-2ubuntu0.1) ...
Selecting previously unselected package libnsl-dev:amd64.
Preparing to unpack .../046-libnsl-dev_1.3.0-2build2_amd64.deb ...
Unpacking libnsl-dev:amd64 (1.3.0-2build2) ...
Selecting previously unselected package libc6-dev:amd64.
Preparing to unpack .../047-libc6-dev_2.35-0ubuntu3.14_amd64.deb ...
Unpacking libc6-dev:amd64 (2.35-0ubuntu3.14) ...
Selecting previously unselected package gcc-11-base:amd64.
Preparing to unpack .../048-gcc-11-base_11.4.0-1ubuntu1~22.04.3_amd64.deb ...
Unpacking gcc-11-base:amd64 (11.4.0-1ubuntu1~22.04.3) ...
Selecting previously unselected package libisl23:amd64.
Preparing to unpack .../049-libisl23_0.24-2build1_amd64.deb ...
Unpacking libisl23:amd64 (0.24-2build1) ...
Selecting previously unselected package libmpc3:amd64.
Preparing to unpack .../050-libmpc3_1.2.1-2build1_amd64.deb ...
Unpacking libmpc3:amd64 (1.2.1-2build1) ...
Selecting previously unselected package cpp-11.
Preparing to unpack .../051-cpp-11_11.4.0-1ubuntu1~22.04.3_amd64.deb ...
Unpacking cpp-11 (11.4.0-1ubuntu1~22.04.3) ...
Selecting previously unselected package cpp.
Preparing to unpack .../052-cpp_4%3a11.2.0-1ubuntu1_amd64.deb ...
Unpacking cpp (4:11.2.0-1ubuntu1) ...
Selecting previously unselected package libcc1-0:amd64.
Preparing to unpack .../053-libcc1-0_12.3.0-1ubuntu1~22.04.3_amd64.deb ...
Unpacking libcc1-0:amd64 (12.3.0-1ubuntu1~22.04.3) ...
Selecting previously unselected package libgomp1:amd64.
Preparing to unpack .../054-libgomp1_12.3.0-1ubuntu1~22.04.3_amd64.deb ...
Unpacking libgomp1:amd64 (12.3.0-1ubuntu1~22.04.3) ...
Selecting previously unselected package libitm1:amd64.
Preparing to unpack .../055-libitm1_12.3.0-1ubuntu1~22.04.3_amd64.deb ...
Unpacking libitm1:amd64 (12.3.0-1ubuntu1~22.04.3) ...
Selecting previously unselected package libatomic1:amd64.
Preparing to unpack .../056-libatomic1_12.3.0-1ubuntu1~22.04.3_amd64.deb ...
Unpacking libatomic1:amd64 (12.3.0-1ubuntu1~22.04.3) ...
Selecting previously unselected package libasan6:amd64.
Preparing to unpack .../057-libasan6_11.4.0-1ubuntu1~22.04.3_amd64.deb ...
Unpacking libasan6:amd64 (11.4.0-1ubuntu1~22.04.3) ...
Selecting previously unselected package liblsan0:amd64.
Preparing to unpack .../058-liblsan0_12.3.0-1ubuntu1~22.04.3_amd64.deb ...
Unpacking liblsan0:amd64 (12.3.0-1ubuntu1~22.04.3) ...
Selecting previously unselected package libtsan0:amd64.
Preparing to unpack .../059-libtsan0_11.4.0-1ubuntu1~22.04.3_amd64.deb ...
Unpacking libtsan0:amd64 (11.4.0-1ubuntu1~22.04.3) ...
Selecting previously unselected package libubsan1:amd64.
Preparing to unpack .../060-libubsan1_12.3.0-1ubuntu1~22.04.3_amd64.deb ...
Unpacking libubsan1:amd64 (12.3.0-1ubuntu1~22.04.3) ...
Selecting previously unselected package libquadmath0:amd64.
Preparing to unpack .../061-libquadmath0_12.3.0-1ubuntu1~22.04.3_amd64.deb ...
Unpacking libquadmath0:amd64 (12.3.0-1ubuntu1~22.04.3) ...
Selecting previously unselected package libgcc-11-dev:amd64.
Preparing to unpack .../062-libgcc-11-dev_11.4.0-1ubuntu1~22.04.3_amd64.deb ...
Unpacking libgcc-11-dev:amd64 (11.4.0-1ubuntu1~22.04.3) ...
Selecting previously unselected package gcc-11.
Preparing to unpack .../063-gcc-11_11.4.0-1ubuntu1~22.04.3_amd64.deb ...
Unpacking gcc-11 (11.4.0-1ubuntu1~22.04.3) ...
Selecting previously unselected package gcc.
Preparing to unpack .../064-gcc_4%3a11.2.0-1ubuntu1_amd64.deb ...
Unpacking gcc (4:11.2.0-1ubuntu1) ...
Selecting previously unselected package libstdc++-11-dev:amd64.
Preparing to unpack .../065-libstdc++-11-dev_11.4.0-1ubuntu1~22.04.3_amd64.deb ...
Unpacking libstdc++-11-dev:amd64 (11.4.0-1ubuntu1~22.04.3) ...
Selecting previously unselected package g++-11.
Preparing to unpack .../066-g++-11_11.4.0-1ubuntu1~22.04.3_amd64.deb ...
Unpacking g++-11 (11.4.0-1ubuntu1~22.04.3) ...
Selecting previously unselected package g++.
Preparing to unpack .../067-g++_4%3a11.2.0-1ubuntu1_amd64.deb ...
Unpacking g++ (4:11.2.0-1ubuntu1) ...
Selecting previously unselected package make.
Preparing to unpack .../068-make_4.3-4.1build1_amd64.deb ...
Unpacking make (4.3-4.1build1) ...
Selecting previously unselected package libdpkg-perl.
Preparing to unpack .../069-libdpkg-perl_1.21.1ubuntu2.6_all.deb ...
Unpacking libdpkg-perl (1.21.1ubuntu2.6) ...
Selecting previously unselected package bzip2.
Preparing to unpack .../070-bzip2_1.0.8-5build1_amd64.deb ...
Unpacking bzip2 (1.0.8-5build1) ...
Selecting previously unselected package lto-disabled-list.
Preparing to unpack .../071-lto-disabled-list_24_all.deb ...
Unpacking lto-disabled-list (24) ...
Selecting previously unselected package dpkg-dev.
Preparing to unpack .../072-dpkg-dev_1.21.1ubuntu2.6_all.deb ...
Unpacking dpkg-dev (1.21.1ubuntu2.6) ...
Selecting previously unselected package build-essential.
Preparing to unpack .../073-build-essential_12.9ubuntu3_amd64.deb ...
Unpacking build-essential (12.9ubuntu3) ...
Selecting previously unselected package libarchive13:amd64.
Preparing to unpack .../074-libarchive13_3.6.0-1ubuntu1.8_amd64.deb ...
Unpacking libarchive13:amd64 (3.6.0-1ubuntu1.8) ...
Preparing to unpack .../075-curl_7.81.0-1ubuntu1.26_amd64.deb ...
Unpacking curl (7.81.0-1ubuntu1.26) over (7.81.0-1ubuntu1.22) ...
Preparing to unpack .../076-libcurl4_7.81.0-1ubuntu1.26_amd64.deb ...
Unpacking libcurl4:amd64 (7.81.0-1ubuntu1.26) over (7.81.0-1ubuntu1.22) ...
Selecting previously unselected package libjsoncpp25:amd64.
Preparing to unpack .../077-libjsoncpp25_1.9.5-3_amd64.deb ...
Unpacking libjsoncpp25:amd64 (1.9.5-3) ...
Selecting previously unselected package librhash0:amd64.
Preparing to unpack .../078-librhash0_1.4.2-1ubuntu1_amd64.deb ...
Unpacking librhash0:amd64 (1.4.2-1ubuntu1) ...
Selecting previously unselected package dh-elpa-helper.
Preparing to unpack .../079-dh-elpa-helper_2.0.9ubuntu1_all.deb ...
Unpacking dh-elpa-helper (2.0.9ubuntu1) ...
Selecting previously unselected package emacsen-common.
Preparing to unpack .../080-emacsen-common_3.0.4_all.deb ...
Unpacking emacsen-common (3.0.4) ...
Selecting previously unselected package cmake-data.
Preparing to unpack .../081-cmake-data_3.22.1-1ubuntu1.22.04.2_all.deb ...
Unpacking cmake-data (3.22.1-1ubuntu1.22.04.2) ...
Selecting previously unselected package cmake.
Preparing to unpack .../082-cmake_3.22.1-1ubuntu1.22.04.2_amd64.deb ...
Unpacking cmake (3.22.1-1ubuntu1.22.04.2) ...
Selecting previously unselected package mysql-common.
Preparing to unpack .../083-mysql-common_5.8+1.0.8_all.deb ...
Unpacking mysql-common (5.8+1.0.8) ...
Selecting previously unselected package libmysqlclient21:amd64.
Preparing to unpack .../084-libmysqlclient21_8.0.46-0ubuntu0.22.04.3_amd64.deb ...
Unpacking libmysqlclient21:amd64 (8.0.46-0ubuntu0.22.04.3) ...
Selecting previously unselected package libssl-dev:amd64.
Preparing to unpack .../085-libssl-dev_3.0.2-0ubuntu1.26_amd64.deb ...
Unpacking libssl-dev:amd64 (3.0.2-0ubuntu1.26) ...
Selecting previously unselected package libzstd-dev:amd64.
Preparing to unpack .../086-libzstd-dev_1.4.8+dfsg-3build1_amd64.deb ...
Unpacking libzstd-dev:amd64 (1.4.8+dfsg-3build1) ...
Selecting previously unselected package zlib1g-dev:amd64.
Preparing to unpack .../087-zlib1g-dev_1%3a1.2.11.dfsg-2ubuntu9.2_amd64.deb ...
Unpacking zlib1g-dev:amd64 (1:1.2.11.dfsg-2ubuntu9.2) ...
Selecting previously unselected package libmysqlclient-dev.
Preparing to unpack .../088-libmysqlclient-dev_8.0.46-0ubuntu0.22.04.3_amd64.deb ...
Unpacking libmysqlclient-dev (8.0.46-0ubuntu0.22.04.3) ...
Selecting previously unselected package default-libmysqlclient-dev:amd64.
Preparing to unpack .../089-default-libmysqlclient-dev_1.0.8_amd64.deb ...
Unpacking default-libmysqlclient-dev:amd64 (1.0.8) ...
Selecting previously unselected package libllvm14:amd64.
Preparing to unpack .../090-libllvm14_1%3a14.0.0-1ubuntu1.1_amd64.deb ...
Unpacking libllvm14:amd64 (1:14.0.0-1ubuntu1.1) ...
Selecting previously unselected package libclang-cpp14.
Preparing to unpack .../091-libclang-cpp14_1%3a14.0.0-1ubuntu1.1_amd64.deb ...
Unpacking libclang-cpp14 (1:14.0.0-1ubuntu1.1) ...
Selecting previously unselected package libclang1-14.
Preparing to unpack .../092-libclang1-14_1%3a14.0.0-1ubuntu1.1_amd64.deb ...
Unpacking libclang1-14 (1:14.0.0-1ubuntu1.1) ...
Selecting previously unselected package libxapian30:amd64.
Preparing to unpack .../093-libxapian30_1.4.18-4_amd64.deb ...
Unpacking libxapian30:amd64 (1.4.18-4) ...
Selecting previously unselected package doxygen.
Preparing to unpack .../094-doxygen_1.9.1-2ubuntu2_amd64.deb ...
Unpacking doxygen (1.9.1-2ubuntu2) ...
Selecting previously unselected package fonts-lyx.
Preparing to unpack .../095-fonts-lyx_2.3.6-1_all.deb ...
Unpacking fonts-lyx (2.3.6-1) ...
Selecting previously unselected package gdal-data.
Preparing to unpack .../096-gdal-data_3.4.1+dfsg-1build4_all.deb ...
Unpacking gdal-data (3.4.1+dfsg-1build4) ...
Selecting previously unselected package aglfn.
Preparing to unpack .../097-aglfn_1.7+git20191031.4036a9c-2_all.deb ...
Unpacking aglfn (1.7+git20191031.4036a9c-2) ...
Selecting previously unselected package gnuplot-data.
Preparing to unpack .../098-gnuplot-data_5.4.2+dfsg2-2_all.deb ...
Unpacking gnuplot-data (5.4.2+dfsg2-2) ...
Preparing to unpack .../099-libtiff5_4.3.0-6ubuntu0.13_amd64.deb ...
Unpacking libtiff5:amd64 (4.3.0-6ubuntu0.13) over (4.3.0-6ubuntu0.12) ...
Selecting previously unselected package libxpm4:amd64.
Preparing to unpack .../100-libxpm4_1%3a3.5.12-1ubuntu0.22.04.3_amd64.deb ...
Unpacking libxpm4:amd64 (1:3.5.12-1ubuntu0.22.04.3) ...
Selecting previously unselected package libgd3:amd64.
Preparing to unpack .../101-libgd3_2.3.0-2ubuntu2.3_amd64.deb ...
Unpacking libgd3:amd64 (2.3.0-2ubuntu2.3) ...
Selecting previously unselected package liblua5.4-0:amd64.
Preparing to unpack .../102-liblua5.4-0_5.4.4-1_amd64.deb ...
Unpacking liblua5.4-0:amd64 (5.4.4-1) ...
Selecting previously unselected package libqt5printsupport5:amd64.
Preparing to unpack .../103-libqt5printsupport5_5.15.3+dfsg-2ubuntu0.2_amd64.deb ...
Unpacking libqt5printsupport5:amd64 (5.15.3+dfsg-2ubuntu0.2) ...
Selecting previously unselected package libwxbase3.0-0v5:amd64.
Preparing to unpack .../104-libwxbase3.0-0v5_3.0.5.1+dfsg-4_amd64.deb ...
Unpacking libwxbase3.0-0v5:amd64 (3.0.5.1+dfsg-4) ...
Selecting previously unselected package libnotify4:amd64.
Preparing to unpack .../105-libnotify4_0.7.9-3ubuntu5.22.04.1_amd64.deb ...
Unpacking libnotify4:amd64 (0.7.9-3ubuntu5.22.04.1) ...
Selecting previously unselected package libwxgtk3.0-gtk3-0v5:amd64.
Preparing to unpack .../106-libwxgtk3.0-gtk3-0v5_3.0.5.1+dfsg-4_amd64.deb ...
Unpacking libwxgtk3.0-gtk3-0v5:amd64 (3.0.5.1+dfsg-4) ...
Selecting previously unselected package gnuplot-qt.
Preparing to unpack .../107-gnuplot-qt_5.4.2+dfsg2-2_amd64.deb ...
Unpacking gnuplot-qt (5.4.2+dfsg2-2) ...
Selecting previously unselected package gnuplot.
Preparing to unpack .../108-gnuplot_5.4.2+dfsg2-2_all.deb ...
Unpacking gnuplot (5.4.2+dfsg2-2) ...
Selecting previously unselected package googletest.
Preparing to unpack .../109-googletest_1.11.0-3_all.deb ...
Unpacking googletest (1.11.0-3) ...
Selecting previously unselected package hdf5-helpers.
Preparing to unpack .../110-hdf5-helpers_1.10.7+repack-4ubuntu2_amd64.deb ...
Unpacking hdf5-helpers (1.10.7+repack-4ubuntu2) ...
Selecting previously unselected package icu-devtools.
Preparing to unpack .../111-icu-devtools_70.1-2_amd64.deb ...
Unpacking icu-devtools (70.1-2) ...
Selecting previously unselected package libjson-perl.
Preparing to unpack .../112-libjson-perl_4.04000-1_all.deb ...
Unpacking libjson-perl (4.04000-1) ...
Selecting previously unselected package libperlio-gzip-perl.
Preparing to unpack .../113-libperlio-gzip-perl_0.19-1build8_amd64.deb ...
Unpacking libperlio-gzip-perl (0.19-1build8) ...
Selecting previously unselected package lcov.
Preparing to unpack .../114-lcov_1.15-1_all.deb ...
Unpacking lcov (1.15-1) ...
Selecting previously unselected package libaec0:amd64.
Preparing to unpack .../115-libaec0_1.0.6-1_amd64.deb ...
Unpacking libaec0:amd64 (1.0.6-1) ...
Selecting previously unselected package libaom3:amd64.
Preparing to unpack .../116-libaom3_3.3.0-1ubuntu0.1_amd64.deb ...
Unpacking libaom3:amd64 (3.3.0-1ubuntu0.1) ...
Selecting previously unselected package libaom-dev:amd64.
Preparing to unpack .../117-libaom-dev_3.3.0-1ubuntu0.1_amd64.deb ...
Unpacking libaom-dev:amd64 (3.3.0-1ubuntu0.1) ...
Selecting previously unselected package libblas3:amd64.
Preparing to unpack .../118-libblas3_3.10.0-2ubuntu1_amd64.deb ...
Unpacking libblas3:amd64 (3.10.0-2ubuntu1) ...
Selecting previously unselected package libgfortran5:amd64.
Preparing to unpack .../119-libgfortran5_12.3.0-1ubuntu1~22.04.3_amd64.deb ...
Unpacking libgfortran5:amd64 (12.3.0-1ubuntu1~22.04.3) ...
Selecting previously unselected package libopenblas0-pthread:amd64.
Preparing to unpack .../120-libopenblas0-pthread_0.3.20+ds-1_amd64.deb ...
Unpacking libopenblas0-pthread:amd64 (0.3.20+ds-1) ...
Selecting previously unselected package liblapack3:amd64.
Preparing to unpack .../121-liblapack3_3.10.0-2ubuntu1_amd64.deb ...
Unpacking liblapack3:amd64 (3.10.0-2ubuntu1) ...
Selecting previously unselected package libarpack2:amd64.
Preparing to unpack .../122-libarpack2_3.8.0-1_amd64.deb ...
Unpacking libarpack2:amd64 (3.8.0-1) ...
Selecting previously unselected package libsuperlu5:amd64.
Preparing to unpack .../123-libsuperlu5_5.3.0+dfsg1-2_amd64.deb ...
Unpacking libsuperlu5:amd64 (5.3.0+dfsg1-2) ...
Selecting previously unselected package libarmadillo10.
Preparing to unpack .../124-libarmadillo10_1%3a10.8.2+dfsg-1_amd64.deb ...
Unpacking libarmadillo10 (1:10.8.2+dfsg-1) ...
Selecting previously unselected package libopenblas-pthread-dev:amd64.
Preparing to unpack .../125-libopenblas-pthread-dev_0.3.20+ds-1_amd64.deb ...
Unpacking libopenblas-pthread-dev:amd64 (0.3.20+ds-1) ...
Selecting previously unselected package libarpack2-dev:amd64.
Preparing to unpack .../126-libarpack2-dev_3.8.0-1_amd64.deb ...
Unpacking libarpack2-dev:amd64 (3.8.0-1) ...
Selecting previously unselected package libsz2:amd64.
Preparing to unpack .../127-libsz2_1.0.6-1_amd64.deb ...
Unpacking libsz2:amd64 (1.0.6-1) ...
Selecting previously unselected package libhdf5-103-1:amd64.
Preparing to unpack .../128-libhdf5-103-1_1.10.7+repack-4ubuntu2_amd64.deb ...
Unpacking libhdf5-103-1:amd64 (1.10.7+repack-4ubuntu2) ...
Selecting previously unselected package libhdf5-fortran-102:amd64.
Preparing to unpack .../129-libhdf5-fortran-102_1.10.7+repack-4ubuntu2_amd64.deb ...
Unpacking libhdf5-fortran-102:amd64 (1.10.7+repack-4ubuntu2) ...
Selecting previously unselected package libhdf5-hl-100:amd64.
Preparing to unpack .../130-libhdf5-hl-100_1.10.7+repack-4ubuntu2_amd64.deb ...
Unpacking libhdf5-hl-100:amd64 (1.10.7+repack-4ubuntu2) ...
Selecting previously unselected package libhdf5-hl-fortran-100:amd64.
Preparing to unpack .../131-libhdf5-hl-fortran-100_1.10.7+repack-4ubuntu2_amd64.deb ...
Unpacking libhdf5-hl-fortran-100:amd64 (1.10.7+repack-4ubuntu2) ...
Selecting previously unselected package libhdf5-cpp-103-1:amd64.
Preparing to unpack .../132-libhdf5-cpp-103-1_1.10.7+repack-4ubuntu2_amd64.deb ...
Unpacking libhdf5-cpp-103-1:amd64 (1.10.7+repack-4ubuntu2) ...
Selecting previously unselected package libhdf5-hl-cpp-100:amd64.
Preparing to unpack .../133-libhdf5-hl-cpp-100_1.10.7+repack-4ubuntu2_amd64.deb ...
Unpacking libhdf5-hl-cpp-100:amd64 (1.10.7+repack-4ubuntu2) ...
Selecting previously unselected package libjpeg-turbo8-dev:amd64.
Preparing to unpack .../134-libjpeg-turbo8-dev_2.1.2-0ubuntu1_amd64.deb ...
Unpacking libjpeg-turbo8-dev:amd64 (2.1.2-0ubuntu1) ...
Selecting previously unselected package libjpeg8-dev:amd64.
Preparing to unpack .../135-libjpeg8-dev_8c-2ubuntu10_amd64.deb ...
Unpacking libjpeg8-dev:amd64 (8c-2ubuntu10) ...
Selecting previously unselected package libjpeg-dev:amd64.
Preparing to unpack .../136-libjpeg-dev_8c-2ubuntu10_amd64.deb ...
Unpacking libjpeg-dev:amd64 (8c-2ubuntu10) ...
Selecting previously unselected package libaec-dev:amd64.
Preparing to unpack .../137-libaec-dev_1.0.6-1_amd64.deb ...
Unpacking libaec-dev:amd64 (1.0.6-1) ...
Selecting previously unselected package libcurl4-openssl-dev:amd64.
Preparing to unpack .../138-libcurl4-openssl-dev_7.81.0-1ubuntu1.26_amd64.deb ...
Unpacking libcurl4-openssl-dev:amd64 (7.81.0-1ubuntu1.26) ...
Selecting previously unselected package libhdf5-dev.
Preparing to unpack .../139-libhdf5-dev_1.10.7+repack-4ubuntu2_amd64.deb ...
Unpacking libhdf5-dev (1.10.7+repack-4ubuntu2) ...
Selecting previously unselected package libopenblas0:amd64.
Preparing to unpack .../140-libopenblas0_0.3.20+ds-1_amd64.deb ...
Unpacking libopenblas0:amd64 (0.3.20+ds-1) ...
Selecting previously unselected package libopenblas-dev:amd64.
Preparing to unpack .../141-libopenblas-dev_0.3.20+ds-1_amd64.deb ...
Unpacking libopenblas-dev:amd64 (0.3.20+ds-1) ...
Selecting previously unselected package libsuperlu-dev:amd64.
Preparing to unpack .../142-libsuperlu-dev_5.3.0+dfsg1-2_amd64.deb ...
Unpacking libsuperlu-dev:amd64 (5.3.0+dfsg1-2) ...
Selecting previously unselected package libarmadillo-dev.
Preparing to unpack .../143-libarmadillo-dev_1%3a10.8.2+dfsg-1_amd64.deb ...
Unpacking libarmadillo-dev (1:10.8.2+dfsg-1) ...
Selecting previously unselected package libsnappy1v5:amd64.
Preparing to unpack .../144-libsnappy1v5_1.1.8-1build3_amd64.deb ...
Unpacking libsnappy1v5:amd64 (1.1.8-1build3) ...
Selecting previously unselected package libblosc1:amd64.
Preparing to unpack .../145-libblosc1_1.21.1+ds2-2_amd64.deb ...
Unpacking libblosc1:amd64 (1.21.1+ds2-2) ...
Selecting previously unselected package libblosc-dev.
Preparing to unpack .../146-libblosc-dev_1.21.1+ds2-2_amd64.deb ...
Unpacking libblosc-dev (1.21.1+ds2-2) ...
Selecting previously unselected package libboost1.74-dev:amd64.
Preparing to unpack .../147-libboost1.74-dev_1.74.0-14ubuntu3_amd64.deb ...
Unpacking libboost1.74-dev:amd64 (1.74.0-14ubuntu3) ...
Selecting previously unselected package libboost-dev:amd64.
Preparing to unpack .../148-libboost-dev_1.74.0.3ubuntu7_amd64.deb ...
Unpacking libboost-dev:amd64 (1.74.0.3ubuntu7) ...
Selecting previously unselected package libcfitsio9:amd64.
Preparing to unpack .../149-libcfitsio9_4.0.0-1_amd64.deb ...
Unpacking libcfitsio9:amd64 (4.0.0-1) ...
Selecting previously unselected package libcfitsio-dev:amd64.
Preparing to unpack .../150-libcfitsio-dev_4.0.0-1_amd64.deb ...
Unpacking libcfitsio-dev:amd64 (4.0.0-1) ...
Selecting previously unselected package libcharls2:amd64.
Preparing to unpack .../151-libcharls2_2.3.4-1_amd64.deb ...
Unpacking libcharls2:amd64 (2.3.4-1) ...
Selecting previously unselected package libcharls-dev:amd64.
Preparing to unpack .../152-libcharls-dev_2.3.4-1_amd64.deb ...
Unpacking libcharls-dev:amd64 (2.3.4-1) ...
Selecting previously unselected package libdav1d5:amd64.
Preparing to unpack .../153-libdav1d5_0.9.2-1_amd64.deb ...
Unpacking libdav1d5:amd64 (0.9.2-1) ...
Selecting previously unselected package libdav1d-dev:amd64.
Preparing to unpack .../154-libdav1d-dev_0.9.2-1_amd64.deb ...
Unpacking libdav1d-dev:amd64 (0.9.2-1) ...
Selecting previously unselected package libde265-0:amd64.
Preparing to unpack .../155-libde265-0_1.0.8-1ubuntu0.3_amd64.deb ...
Unpacking libde265-0:amd64 (1.0.8-1ubuntu0.3) ...
Selecting previously unselected package libde265-dev:amd64.
Preparing to unpack .../156-libde265-dev_1.0.8-1ubuntu0.3_amd64.deb ...
Unpacking libde265-dev:amd64 (1.0.8-1ubuntu0.3) ...
Selecting previously unselected package libdeflate-dev:amd64.
Preparing to unpack .../157-libdeflate-dev_1.10-2_amd64.deb ...
Unpacking libdeflate-dev:amd64 (1.10-2) ...
Selecting previously unselected package libexpat1-dev:amd64.
Preparing to unpack .../158-libexpat1-dev_2.4.7-1ubuntu0.7_amd64.deb ...
Unpacking libexpat1-dev:amd64 (2.4.7-1ubuntu0.7) ...
Selecting previously unselected package libfyba0:amd64.
Preparing to unpack .../159-libfyba0_4.1.1-7_amd64.deb ...
Unpacking libfyba0:amd64 (4.1.1-7) ...
Selecting previously unselected package libfyba-dev:amd64.
Preparing to unpack .../160-libfyba-dev_4.1.1-7_amd64.deb ...
Unpacking libfyba-dev:amd64 (4.1.1-7) ...
Selecting previously unselected package libfreexl1:amd64.
Preparing to unpack .../161-libfreexl1_1.0.6-1_amd64.deb ...
Unpacking libfreexl1:amd64 (1.0.6-1) ...
Selecting previously unselected package libgeos3.10.2:amd64.
Preparing to unpack .../162-libgeos3.10.2_3.10.2-1_amd64.deb ...
Unpacking libgeos3.10.2:amd64 (3.10.2-1) ...
Selecting previously unselected package libgeos-c1v5:amd64.
Preparing to unpack .../163-libgeos-c1v5_3.10.2-1_amd64.deb ...
Unpacking libgeos-c1v5:amd64 (3.10.2-1) ...
Selecting previously unselected package proj-data.
Preparing to unpack .../164-proj-data_8.2.1-1_all.deb ...
Unpacking proj-data (8.2.1-1) ...
Selecting previously unselected package libproj22:amd64.
Preparing to unpack .../165-libproj22_8.2.1-1_amd64.deb ...
Unpacking libproj22:amd64 (8.2.1-1) ...
Selecting previously unselected package libgeotiff5:amd64.
Preparing to unpack .../166-libgeotiff5_1.7.0-2build1_amd64.deb ...
Unpacking libgeotiff5:amd64 (1.7.0-2build1) ...
Selecting previously unselected package libgif7:amd64.
Preparing to unpack .../167-libgif7_5.1.9-2ubuntu0.3_amd64.deb ...
Unpacking libgif7:amd64 (5.1.9-2ubuntu0.3) ...
Selecting previously unselected package libhdf4-0-alt.
Preparing to unpack .../168-libhdf4-0-alt_4.2.15-4_amd64.deb ...
Unpacking libhdf4-0-alt (4.2.15-4) ...
Selecting previously unselected package libx265-199:amd64.
Preparing to unpack .../169-libx265-199_3.5-2_amd64.deb ...
Unpacking libx265-199:amd64 (3.5-2) ...
Selecting previously unselected package libheif1:amd64.
Preparing to unpack .../170-libheif1_1.12.0-2build1_amd64.deb ...
Unpacking libheif1:amd64 (1.12.0-2build1) ...
Selecting previously unselected package libminizip1:amd64.
Preparing to unpack .../171-libminizip1_1.1-8build1_amd64.deb ...
Unpacking libminizip1:amd64 (1.1-8build1) ...
Selecting previously unselected package liburiparser1:amd64.
Preparing to unpack .../172-liburiparser1_0.9.6+dfsg-1_amd64.deb ...
Unpacking liburiparser1:amd64 (0.9.6+dfsg-1) ...
Selecting previously unselected package libkmlbase1:amd64.
Preparing to unpack .../173-libkmlbase1_1.3.0-9_amd64.deb ...
Unpacking libkmlbase1:amd64 (1.3.0-9) ...
Selecting previously unselected package libkmldom1:amd64.
Preparing to unpack .../174-libkmldom1_1.3.0-9_amd64.deb ...
Unpacking libkmldom1:amd64 (1.3.0-9) ...
Selecting previously unselected package libkmlengine1:amd64.
Preparing to unpack .../175-libkmlengine1_1.3.0-9_amd64.deb ...
Unpacking libkmlengine1:amd64 (1.3.0-9) ...
Selecting previously unselected package libnetcdf19:amd64.
Preparing to unpack .../176-libnetcdf19_1%3a4.8.1-1_amd64.deb ...
Unpacking libnetcdf19:amd64 (1:4.8.1-1) ...
Selecting previously unselected package libltdl7:amd64.
Preparing to unpack .../177-libltdl7_2.4.6-15build2_amd64.deb ...
Unpacking libltdl7:amd64 (2.4.6-15build2) ...
Selecting previously unselected package libodbc2:amd64.
Preparing to unpack .../178-libodbc2_2.3.9-5ubuntu0.1_amd64.deb ...
Unpacking libodbc2:amd64 (2.3.9-5ubuntu0.1) ...
Selecting previously unselected package unixodbc-common.
Preparing to unpack .../179-unixodbc-common_2.3.9-5ubuntu0.1_all.deb ...
Unpacking unixodbc-common (2.3.9-5ubuntu0.1) ...
Selecting previously unselected package libodbcinst2:amd64.
Preparing to unpack .../180-libodbcinst2_2.3.9-5ubuntu0.1_amd64.deb ...
Unpacking libodbcinst2:amd64 (2.3.9-5ubuntu0.1) ...
Selecting previously unselected package libogdi4.1.
Preparing to unpack .../181-libogdi4.1_4.1.0+ds-5_amd64.deb ...
Unpacking libogdi4.1 (4.1.0+ds-5) ...
Selecting previously unselected package libopenjp2-7:amd64.
Preparing to unpack .../182-libopenjp2-7_2.4.0-6ubuntu0.5_amd64.deb ...
Unpacking libopenjp2-7:amd64 (2.4.0-6ubuntu0.5) ...
Selecting previously unselected package libnspr4:amd64.
Preparing to unpack .../183-libnspr4_2%3a4.35-0ubuntu0.22.04.1_amd64.deb ...
Unpacking libnspr4:amd64 (2:4.35-0ubuntu0.22.04.1) ...
Selecting previously unselected package libnss3:amd64.
Preparing to unpack .../184-libnss3_2%3a3.98-0ubuntu0.22.04.4_amd64.deb ...
Unpacking libnss3:amd64 (2:3.98-0ubuntu0.22.04.4) ...
Selecting previously unselected package libpoppler118:amd64.
Preparing to unpack .../185-libpoppler118_22.02.0-2ubuntu0.13_amd64.deb ...
Unpacking libpoppler118:amd64 (22.02.0-2ubuntu0.13) ...
Selecting previously unselected package libpq5:amd64.
Preparing to unpack .../186-libpq5_14.24-0ubuntu0.22.04.1_amd64.deb ...
Unpacking libpq5:amd64 (14.24-0ubuntu0.22.04.1) ...
Selecting previously unselected package libqhull-r8.0:amd64.
Preparing to unpack .../187-libqhull-r8.0_2020.2-4_amd64.deb ...
Unpacking libqhull-r8.0:amd64 (2020.2-4) ...
Selecting previously unselected package librttopo1:amd64.
Preparing to unpack .../188-librttopo1_1.1.0-2_amd64.deb ...
Unpacking librttopo1:amd64 (1.1.0-2) ...
Selecting previously unselected package libspatialite7:amd64.
Preparing to unpack .../189-libspatialite7_5.0.1-2build2_amd64.deb ...
Unpacking libspatialite7:amd64 (5.0.1-2build2) ...
Selecting previously unselected package libxerces-c3.2:amd64.
Preparing to unpack .../190-libxerces-c3.2_3.2.3+debian-3ubuntu0.1_amd64.deb ...
Unpacking libxerces-c3.2:amd64 (3.2.3+debian-3ubuntu0.1) ...
Selecting previously unselected package libgdal30.
Preparing to unpack .../191-libgdal30_3.4.1+dfsg-1build4_amd64.deb ...
Unpacking libgdal30 (3.4.1+dfsg-1build4) ...
Selecting previously unselected package libgeos-dev.
Preparing to unpack .../192-libgeos-dev_3.10.2-1_amd64.deb ...
Unpacking libgeos-dev (3.10.2-1) ...
Selecting previously unselected package libgif-dev.
Preparing to unpack .../193-libgif-dev_5.1.9-2ubuntu0.3_amd64.deb ...
Unpacking libgif-dev (5.1.9-2ubuntu0.3) ...
Selecting previously unselected package libgtest-dev:amd64.
Preparing to unpack .../194-libgtest-dev_1.11.0-3_amd64.deb ...
Unpacking libgtest-dev:amd64 (1.11.0-3) ...
Selecting previously unselected package libx265-dev:amd64.
Preparing to unpack .../195-libx265-dev_3.5-2_amd64.deb ...
Unpacking libx265-dev:amd64 (3.5-2) ...
Selecting previously unselected package libheif-dev:amd64.
Preparing to unpack .../196-libheif-dev_1.12.0-2build1_amd64.deb ...
Unpacking libheif-dev:amd64 (1.12.0-2build1) ...
Selecting previously unselected package libicu-dev:amd64.
Preparing to unpack .../197-libicu-dev_70.1-2_amd64.deb ...
Unpacking libicu-dev:amd64 (70.1-2) ...
Selecting previously unselected package libimagequant0:amd64.
Preparing to unpack .../198-libimagequant0_2.17.0-1_amd64.deb ...
Unpacking libimagequant0:amd64 (2.17.0-1) ...
Selecting previously unselected package libjs-jquery.
Preparing to unpack .../199-libjs-jquery_3.6.0+dfsg+~3.5.13-1_all.deb ...
Unpacking libjs-jquery (3.6.0+dfsg+~3.5.13-1) ...
Selecting previously unselected package libjs-jquery-ui.
Preparing to unpack .../200-libjs-jquery-ui_1.13.1+dfsg-1_all.deb ...
Unpacking libjs-jquery-ui (1.13.1+dfsg-1) ...
Selecting previously unselected package libjs-underscore.
Preparing to unpack .../201-libjs-underscore_1.13.2~dfsg-2_all.deb ...
Unpacking libjs-underscore (1.13.2~dfsg-2) ...
Selecting previously unselected package libjs-sphinxdoc.
Preparing to unpack .../202-libjs-sphinxdoc_4.3.2-1_all.deb ...
Unpacking libjs-sphinxdoc (4.3.2-1) ...
Selecting previously unselected package libkmlconvenience1:amd64.
Preparing to unpack .../203-libkmlconvenience1_1.3.0-9_amd64.deb ...
Unpacking libkmlconvenience1:amd64 (1.3.0-9) ...
Selecting previously unselected package libkmlregionator1:amd64.
Preparing to unpack .../204-libkmlregionator1_1.3.0-9_amd64.deb ...
Unpacking libkmlregionator1:amd64 (1.3.0-9) ...
Selecting previously unselected package libkmlxsd1:amd64.
Preparing to unpack .../205-libkmlxsd1_1.3.0-9_amd64.deb ...
Unpacking libkmlxsd1:amd64 (1.3.0-9) ...
Selecting previously unselected package liblbfgsb0:amd64.
Preparing to unpack .../206-liblbfgsb0_3.0+dfsg.3-10_amd64.deb ...
Unpacking liblbfgsb0:amd64 (3.0+dfsg.3-10) ...
Selecting previously unselected package libltdl-dev:amd64.
Preparing to unpack .../207-libltdl-dev_2.4.6-15build2_amd64.deb ...
Unpacking libltdl-dev:amd64 (2.4.6-15build2) ...
Selecting previously unselected package libminizip-dev:amd64.
Preparing to unpack .../208-libminizip-dev_1.1-8build1_amd64.deb ...
Unpacking libminizip-dev:amd64 (1.1-8build1) ...
Selecting previously unselected package libnetcdf-dev.
Preparing to unpack .../209-libnetcdf-dev_1%3a4.8.1-1_amd64.deb ...
Unpacking libnetcdf-dev (1:4.8.1-1) ...
Selecting previously unselected package libodbccr2:amd64.
Preparing to unpack .../210-libodbccr2_2.3.9-5ubuntu0.1_amd64.deb ...
Unpacking libodbccr2:amd64 (2.3.9-5ubuntu0.1) ...
Selecting previously unselected package libogdi-dev.
Preparing to unpack .../211-libogdi-dev_4.1.0+ds-5_amd64.deb ...
Unpacking libogdi-dev (4.1.0+ds-5) ...
Selecting previously unselected package libpcre2-32-0:amd64.
Preparing to unpack .../212-libpcre2-32-0_10.39-3ubuntu0.1_amd64.deb ...
Unpacking libpcre2-32-0:amd64 (10.39-3ubuntu0.1) ...
Selecting previously unselected package libpcre2-posix3:amd64.
Preparing to unpack .../213-libpcre2-posix3_10.39-3ubuntu0.1_amd64.deb ...
Unpacking libpcre2-posix3:amd64 (10.39-3ubuntu0.1) ...
Selecting previously unselected package libpcre2-dev:amd64.
Preparing to unpack .../214-libpcre2-dev_10.39-3ubuntu0.1_amd64.deb ...
Unpacking libpcre2-dev:amd64 (10.39-3ubuntu0.1) ...
Selecting previously unselected package libpng-dev:amd64.
Preparing to unpack .../215-libpng-dev_1.6.37-3ubuntu0.6_amd64.deb ...
Unpacking libpng-dev:amd64 (1.6.37-3ubuntu0.6) ...
Selecting previously unselected package libpoppler-dev:amd64.
Preparing to unpack .../216-libpoppler-dev_22.02.0-2ubuntu0.13_amd64.deb ...
Unpacking libpoppler-dev:amd64 (22.02.0-2ubuntu0.13) ...
Selecting previously unselected package libpoppler-private-dev:amd64.
Preparing to unpack .../217-libpoppler-private-dev_22.02.0-2ubuntu0.13_amd64.deb ...
Unpacking libpoppler-private-dev:amd64 (22.02.0-2ubuntu0.13) ...
Selecting previously unselected package libpq-dev.
Preparing to unpack .../218-libpq-dev_14.24-0ubuntu0.22.04.1_amd64.deb ...
Unpacking libpq-dev (14.24-0ubuntu0.22.04.1) ...
Selecting previously unselected package libpython3.10-dev:amd64.
Preparing to unpack .../219-libpython3.10-dev_3.10.12-1~22.04.16_amd64.deb ...
Unpacking libpython3.10-dev:amd64 (3.10.12-1~22.04.16) ...
Selecting previously unselected package libpython3-dev:amd64.
Preparing to unpack .../220-libpython3-dev_3.10.6-1~22.04.1_amd64.deb ...
Unpacking libpython3-dev:amd64 (3.10.6-1~22.04.1) ...
Selecting previously unselected package libqhull8.0:amd64.
Preparing to unpack .../221-libqhull8.0_2020.2-4_amd64.deb ...
Unpacking libqhull8.0:amd64 (2020.2-4) ...
Selecting previously unselected package libqhullcpp8.0:amd64.
Preparing to unpack .../222-libqhullcpp8.0_2020.2-4_amd64.deb ...
Unpacking libqhullcpp8.0:amd64 (2020.2-4) ...
Selecting previously unselected package libqhull-dev:amd64.
Preparing to unpack .../223-libqhull-dev_2020.2-4_amd64.deb ...
Unpacking libqhull-dev:amd64 (2020.2-4) ...
Selecting previously unselected package libraqm0:amd64.
Preparing to unpack .../224-libraqm0_0.7.0-4ubuntu1_amd64.deb ...
Unpacking libraqm0:amd64 (0.7.0-4ubuntu1) ...
Selecting previously unselected package librttopo-dev:amd64.
Preparing to unpack .../225-librttopo-dev_1.1.0-2_amd64.deb ...
Unpacking librttopo-dev:amd64 (1.1.0-2) ...
Selecting previously unselected package libsqlite3-dev:amd64.
Preparing to unpack .../226-libsqlite3-dev_3.37.2-2ubuntu0.7_amd64.deb ...
Unpacking libsqlite3-dev:amd64 (3.37.2-2ubuntu0.7) ...
Selecting previously unselected package libtbbmalloc2:amd64.
Preparing to unpack .../227-libtbbmalloc2_2021.5.0-7ubuntu2_amd64.deb ...
Unpacking libtbbmalloc2:amd64 (2021.5.0-7ubuntu2) ...
Selecting previously unselected package libtbb12:amd64.
Preparing to unpack .../228-libtbb12_2021.5.0-7ubuntu2_amd64.deb ...
Unpacking libtbb12:amd64 (2021.5.0-7ubuntu2) ...
Selecting previously unselected package libjbig-dev:amd64.
Preparing to unpack .../229-libjbig-dev_2.1-3.1ubuntu0.22.04.1_amd64.deb ...
Unpacking libjbig-dev:amd64 (2.1-3.1ubuntu0.22.04.1) ...
Selecting previously unselected package liblzma-dev:amd64.
Preparing to unpack .../230-liblzma-dev_5.2.5-2ubuntu1.1_amd64.deb ...
Unpacking liblzma-dev:amd64 (5.2.5-2ubuntu1.1) ...
Selecting previously unselected package libtiffxx5:amd64.
Preparing to unpack .../231-libtiffxx5_4.3.0-6ubuntu0.13_amd64.deb ...
Unpacking libtiffxx5:amd64 (4.3.0-6ubuntu0.13) ...
Selecting previously unselected package libtiff-dev:amd64.
Preparing to unpack .../232-libtiff-dev_4.3.0-6ubuntu0.13_amd64.deb ...
Unpacking libtiff-dev:amd64 (4.3.0-6ubuntu0.13) ...
Selecting previously unselected package libtinyxml2-9:amd64.
Preparing to unpack .../233-libtinyxml2-9_9.0.0+dfsg-3_amd64.deb ...
Unpacking libtinyxml2-9:amd64 (9.0.0+dfsg-3) ...
Selecting previously unselected package liburiparser-dev.
Preparing to unpack .../234-liburiparser-dev_0.9.6+dfsg-1_amd64.deb ...
Unpacking liburiparser-dev (0.9.6+dfsg-1) ...
Selecting previously unselected package libwebpdemux2:amd64.
Preparing to unpack .../235-libwebpdemux2_1.2.2-2ubuntu0.22.04.2_amd64.deb ...
Unpacking libwebpdemux2:amd64 (1.2.2-2ubuntu0.22.04.2) ...
Selecting previously unselected package libwebpmux3:amd64.
Preparing to unpack .../236-libwebpmux3_1.2.2-2ubuntu0.22.04.2_amd64.deb ...
Unpacking libwebpmux3:amd64 (1.2.2-2ubuntu0.22.04.2) ...
Selecting previously unselected package libxerces-c-dev:amd64.
Preparing to unpack .../237-libxerces-c-dev_3.2.3+debian-3ubuntu0.1_amd64.deb ...
Unpacking libxerces-c-dev:amd64 (3.2.3+debian-3ubuntu0.1) ...
Selecting previously unselected package libxml2-dev:amd64.
Preparing to unpack .../238-libxml2-dev_2.9.13+dfsg-1ubuntu0.12_amd64.deb ...
Unpacking libxml2-dev:amd64 (2.9.13+dfsg-1ubuntu0.12) ...
Selecting previously unselected package libxsimd-dev:amd64.
Preparing to unpack .../239-libxsimd-dev_7.6.0-2_amd64.deb ...
Unpacking libxsimd-dev:amd64 (7.6.0-2) ...
Selecting previously unselected package libxslt1.1:amd64.
Preparing to unpack .../240-libxslt1.1_1.1.34-4ubuntu0.22.04.5_amd64.deb ...
Unpacking libxslt1.1:amd64 (1.1.34-4ubuntu0.22.04.5) ...
Selecting previously unselected package nlohmann-json3-dev.
Preparing to unpack .../241-nlohmann-json3-dev_3.10.5-2_all.deb ...
Unpacking nlohmann-json3-dev (3.10.5-2) ...
Selecting previously unselected package pkg-config.
Preparing to unpack .../242-pkg-config_0.29.2-1ubuntu3_amd64.deb ...
Unpacking pkg-config (0.29.2-1ubuntu3) ...
Selecting previously unselected package python-matplotlib-data.
Preparing to unpack .../243-python-matplotlib-data_3.5.1-2build1_all.deb ...
Unpacking python-matplotlib-data (3.5.1-2build1) ...
Selecting previously unselected package python3-appdirs.
Preparing to unpack .../244-python3-appdirs_1.4.4-2_all.deb ...
Unpacking python3-appdirs (1.4.4-2) ...
Selecting previously unselected package python3-gast.
Preparing to unpack .../245-python3-gast_0.5.2-2_all.deb ...
Unpacking python3-gast (0.5.2-2) ...
Selecting previously unselected package python3-beniget.
Preparing to unpack .../246-python3-beniget_0.4.1-2_all.deb ...
Unpacking python3-beniget (0.4.1-2) ...
Selecting previously unselected package python3-brotli.
Preparing to unpack .../247-python3-brotli_1.0.9-2build6_amd64.deb ...
Unpacking python3-brotli (1.0.9-2build6) ...
Selecting previously unselected package python3-cycler.
Preparing to unpack .../248-python3-cycler_0.11.0-1_all.deb ...
Unpacking python3-cycler (0.11.0-1) ...
Selecting previously unselected package python3-dateutil.
Preparing to unpack .../249-python3-dateutil_2.8.1-6_all.deb ...
Unpacking python3-dateutil (2.8.1-6) ...
Selecting previously unselected package python3-decorator.
Preparing to unpack .../250-python3-decorator_4.4.2-0ubuntu1_all.deb ...
Unpacking python3-decorator (4.4.2-0ubuntu1) ...
Selecting previously unselected package python3.10-dev.
Preparing to unpack .../251-python3.10-dev_3.10.12-1~22.04.16_amd64.deb ...
Unpacking python3.10-dev (3.10.12-1~22.04.16) ...
Selecting previously unselected package python3-dev.
Preparing to unpack .../252-python3-dev_3.10.6-1~22.04.1_amd64.deb ...
Unpacking python3-dev (3.10.6-1~22.04.1) ...
Selecting previously unselected package python3-numpy.
Preparing to unpack .../253-python3-numpy_1%3a1.21.5-1ubuntu22.04.1_amd64.deb ...
Unpacking python3-numpy (1:1.21.5-1ubuntu22.04.1) ...
Selecting previously unselected package python3-ply.
Preparing to unpack .../254-python3-ply_3.11-5_all.deb ...
Unpacking python3-ply (3.11-5) ...
Selecting previously unselected package python3-pythran.
Preparing to unpack .../255-python3-pythran_0.10.0+ds2-1_amd64.deb ...
Unpacking python3-pythran (0.10.0+ds2-1) ...
Selecting previously unselected package python3-scipy.
Preparing to unpack .../256-python3-scipy_1.8.0-1exp2ubuntu1_amd64.deb ...
Unpacking python3-scipy (1.8.0-1exp2ubuntu1) ...
Selecting previously unselected package python3-ufolib2.
Preparing to unpack .../257-python3-ufolib2_0.13.1+dfsg1-1_all.deb ...
Unpacking python3-ufolib2 (0.13.1+dfsg1-1) ...
Selecting previously unselected package python3-mpmath.
Preparing to unpack .../258-python3-mpmath_1.2.1-2_all.deb ...
Unpacking python3-mpmath (1.2.1-2) ...
Selecting previously unselected package python3-sympy.
Preparing to unpack .../259-python3-sympy_1.9-1_all.deb ...
Unpacking python3-sympy (1.9-1) ...
Selecting previously unselected package python3-fs.
Preparing to unpack .../260-python3-fs_2.4.12-1_all.deb ...
Unpacking python3-fs (2.4.12-1) ...
Selecting previously unselected package python3-lxml:amd64.
Preparing to unpack .../261-python3-lxml_4.8.0-1build1_amd64.deb ...
Unpacking python3-lxml:amd64 (4.8.0-1build1) ...
Selecting previously unselected package python3-lz4.
Preparing to unpack .../262-python3-lz4_3.1.3+dfsg-1build3_amd64.deb ...
Unpacking python3-lz4 (3.1.3+dfsg-1build3) ...
Selecting previously unselected package python3-unicodedata2.
Preparing to unpack .../263-python3-unicodedata2_14.0.0+ds-8_amd64.deb ...
Unpacking python3-unicodedata2 (14.0.0+ds-8) ...
Selecting previously unselected package unicode-data.
Preparing to unpack .../264-unicode-data_14.0.0-1.1_all.deb ...
Unpacking unicode-data (14.0.0-1.1) ...
Selecting previously unselected package python3-fonttools.
Preparing to unpack .../265-python3-fonttools_4.29.1-2build1_amd64.deb ...
Unpacking python3-fonttools (4.29.1-2build1) ...
Selecting previously unselected package python3-kiwisolver.
Preparing to unpack .../266-python3-kiwisolver_1.3.2-1build1_amd64.deb ...
Unpacking python3-kiwisolver (1.3.2-1build1) ...
Selecting previously unselected package python3-pil:amd64.
Preparing to unpack .../267-python3-pil_9.0.1-1ubuntu0.4_amd64.deb ...
Unpacking python3-pil:amd64 (9.0.1-1ubuntu0.4) ...
Selecting previously unselected package python3-tk:amd64.
Preparing to unpack .../268-python3-tk_3.10.8-1~22.04_amd64.deb ...
Unpacking python3-tk:amd64 (3.10.8-1~22.04) ...
Selecting previously unselected package python3-pil.imagetk:amd64.
Preparing to unpack .../269-python3-pil.imagetk_9.0.1-1ubuntu0.4_amd64.deb ...
Unpacking python3-pil.imagetk:amd64 (9.0.1-1ubuntu0.4) ...
Selecting previously unselected package python3-packaging.
Preparing to unpack .../270-python3-packaging_21.3-1_all.deb ...
Unpacking python3-packaging (21.3-1) ...
Selecting previously unselected package python3-matplotlib.
Preparing to unpack .../271-python3-matplotlib_3.5.1-2build1_amd64.deb ...
Unpacking python3-matplotlib (3.5.1-2build1) ...
Selecting previously unselected package python3-wheel.
Preparing to unpack .../272-python3-wheel_0.37.1-2ubuntu0.22.04.1_all.deb ...
Unpacking python3-wheel (0.37.1-2ubuntu0.22.04.1) ...
Selecting previously unselected package python3-pip.
Preparing to unpack .../273-python3-pip_22.0.2+dfsg-1ubuntu0.7_all.deb ...
Unpacking python3-pip (22.0.2+dfsg-1ubuntu0.7) ...
Selecting previously unselected package python3-pip-whl.
Preparing to unpack .../274-python3-pip-whl_22.0.2+dfsg-1ubuntu0.7_all.deb ...
Unpacking python3-pip-whl (22.0.2+dfsg-1ubuntu0.7) ...
Selecting previously unselected package python3-setuptools-whl.
Preparing to unpack .../275-python3-setuptools-whl_59.6.0-1.2ubuntu0.22.04.3_all.deb ...
Unpacking python3-setuptools-whl (59.6.0-1.2ubuntu0.22.04.3) ...
Selecting previously unselected package python3.10-venv.
Preparing to unpack .../276-python3.10-venv_3.10.12-1~22.04.16_amd64.deb ...
Unpacking python3.10-venv (3.10.12-1~22.04.16) ...
Selecting previously unselected package python3-venv.
Preparing to unpack .../277-python3-venv_3.10.6-1~22.04.1_amd64.deb ...
Unpacking python3-venv (3.10.6-1~22.04.1) ...
Selecting previously unselected package swig4.0.
Preparing to unpack .../278-swig4.0_4.0.2-1ubuntu1_amd64.deb ...
Unpacking swig4.0 (4.0.2-1ubuntu1) ...
Selecting previously unselected package swig.
Preparing to unpack .../279-swig_4.0.2-1ubuntu1_all.deb ...
Unpacking swig (4.0.2-1ubuntu1) ...
Selecting previously unselected package libeigen3-dev.
Preparing to unpack .../280-libeigen3-dev_3.4.0-2ubuntu2_all.deb ...
Unpacking libeigen3-dev (3.4.0-2ubuntu2) ...
Selecting previously unselected package libfreexl-dev:amd64.
Preparing to unpack .../281-libfreexl-dev_1.0.6-1_amd64.deb ...
Unpacking libfreexl-dev:amd64 (1.0.6-1) ...
Selecting previously unselected package libproj-dev:amd64.
Preparing to unpack .../282-libproj-dev_8.2.1-1_amd64.deb ...
Unpacking libproj-dev:amd64 (8.2.1-1) ...
Selecting previously unselected package libgeotiff-dev:amd64.
Preparing to unpack .../283-libgeotiff-dev_1.7.0-2build1_amd64.deb ...
Unpacking libgeotiff-dev:amd64 (1.7.0-2build1) ...
Selecting previously unselected package libhdf4-alt-dev.
Preparing to unpack .../284-libhdf4-alt-dev_4.2.15-4_amd64.deb ...
Unpacking libhdf4-alt-dev (4.2.15-4) ...
Selecting previously unselected package libjson-c-dev:amd64.
Preparing to unpack .../285-libjson-c-dev_0.15-3~ubuntu1.22.04.2_amd64.deb ...
Unpacking libjson-c-dev:amd64 (0.15-3~ubuntu1.22.04.2) ...
Selecting previously unselected package libkml-dev:amd64.
Preparing to unpack .../286-libkml-dev_1.3.0-9_amd64.deb ...
Unpacking libkml-dev:amd64 (1.3.0-9) ...
Selecting previously unselected package liblz4-dev:amd64.
Preparing to unpack .../287-liblz4-dev_1.9.3-2build2_amd64.deb ...
Unpacking liblz4-dev:amd64 (1.9.3-2build2) ...
Selecting previously unselected package libopenjp2-7-dev:amd64.
Preparing to unpack .../288-libopenjp2-7-dev_2.4.0-6ubuntu0.5_amd64.deb ...
Unpacking libopenjp2-7-dev:amd64 (2.4.0-6ubuntu0.5) ...
Selecting previously unselected package libspatialite-dev:amd64.
Preparing to unpack .../289-libspatialite-dev_5.0.1-2build2_amd64.deb ...
Unpacking libspatialite-dev:amd64 (5.0.1-2build2) ...
Selecting previously unselected package libwebp-dev:amd64.
Preparing to unpack .../290-libwebp-dev_1.2.2-2ubuntu0.22.04.2_amd64.deb ...
Unpacking libwebp-dev:amd64 (1.2.2-2ubuntu0.22.04.2) ...
Selecting previously unselected package unixodbc-dev:amd64.
Preparing to unpack .../291-unixodbc-dev_2.3.9-5ubuntu0.1_amd64.deb ...
Unpacking unixodbc-dev:amd64 (2.3.9-5ubuntu0.1) ...
Selecting previously unselected package libgdal-dev.
Preparing to unpack .../292-libgdal-dev_3.4.1+dfsg-1build4_amd64.deb ...
Unpacking libgdal-dev (3.4.1+dfsg-1build4) ...
Selecting previously unselected package libtbb-dev:amd64.
Preparing to unpack .../293-libtbb-dev_2021.5.0-7ubuntu2_amd64.deb ...
Unpacking libtbb-dev:amd64 (2021.5.0-7ubuntu2) ...
Selecting previously unselected package libtinyxml2-dev:amd64.
Preparing to unpack .../294-libtinyxml2-dev_9.0.0+dfsg-3_amd64.deb ...
Unpacking libtinyxml2-dev:amd64 (9.0.0+dfsg-3) ...
Setting up libtbbmalloc2:amd64 (2021.5.0-7ubuntu2) ...
Setting up libxapian30:amd64 (1.4.18-4) ...
Setting up gcc-11-base:amd64 (11.4.0-1ubuntu1~22.04.3) ...
Setting up libgeos3.10.2:amd64 (3.10.2-1) ...
Setting up libaom3:amd64 (3.3.0-1ubuntu0.1) ...
Setting up libice6:amd64 (2:1.0.10-1build2) ...
Setting up mysql-common (5.8+1.0.8) ...
update-alternatives: using /etc/mysql/my.cnf.fallback to provide /etc/mysql/my.cnf (my.cnf) in auto mode
Setting up libmysqlclient21:amd64 (8.0.46-0ubuntu0.22.04.3) ...
Setting up libdouble-conversion3:amd64 (3.1.7-4) ...
Setting up python3-setuptools-whl (59.6.0-1.2ubuntu0.22.04.3) ...
Setting up lto-disabled-list (24) ...
Setting up libxft2:amd64 (2.3.4-1) ...
Setting up libzstd-dev:amd64 (1.4.8+dfsg-3build1) ...
Setting up libxerces-c3.2:amd64 (3.2.3+debian-3ubuntu0.1) ...
Setting up proj-data (8.2.1-1) ...
Setting up libxpm4:amd64 (1:3.5.12-1ubuntu0.22.04.3) ...
Setting up hdf5-helpers (1.10.7+repack-4ubuntu2) ...
Setting up libxcb-xinput0:amd64 (1.14-3ubuntu3) ...
Setting up libogdi4.1 (4.1.0+ds-5) ...
Setting up libqhull8.0:amd64 (2020.2-4) ...
Setting up python3-pip-whl (22.0.2+dfsg-1ubuntu0.7) ...
Setting up libcharls2:amd64 (2.3.4-1) ...
Setting up libminizip1:amd64 (1.1-8build1) ...
Setting up python3-lz4 (3.1.3+dfsg-1build3) ...
Setting up libjson-c-dev:amd64 (0.15-3~ubuntu1.22.04.2) ...
Setting up python3-unicodedata2 (14.0.0+ds-8) ...
Setting up fonts-lyx (2.3.6-1) ...
Setting up libwebpdemux2:amd64 (1.2.2-2ubuntu0.22.04.2) ...
Setting up python3-ply (3.11-5) ...
Setting up libsqlite3-0:amd64 (3.37.2-2ubuntu0.7) ...
Setting up libxcb-keysyms1:amd64 (0.4.0-1build3) ...
Setting up libxcb-shape0:amd64 (1.14-3ubuntu3) ...
Setting up python3-gast (0.5.2-2) ...
Setting up libpq5:amd64 (14.24-0ubuntu0.22.04.1) ...
Setting up libjbig-dev:amd64 (2.1-3.1ubuntu0.22.04.1) ...
Setting up linux-libc-dev:amd64 (5.15.0-190.200) ...
Setting up m4 (1.4.18-5ubuntu2) ...
Setting up libqhull-r8.0:amd64 (2020.2-4) ...
Setting up libxcb-render-util0:amd64 (0.3.9-1build3) ...
Setting up libtbb12:amd64 (2021.5.0-7ubuntu2) ...
Setting up libxcb-icccm4:amd64 (0.4.1-1.1build2) ...
Setting up libgomp1:amd64 (12.3.0-1ubuntu1~22.04.3) ...
Setting up bzip2 (1.0.8-5build1) ...
Setting up googletest (1.11.0-3) ...
Setting up python3-wheel (0.37.1-2ubuntu0.22.04.1) ...
Setting up libpcre2-16-0:amd64 (10.39-3ubuntu0.1) ...
Setting up libaec0:amd64 (1.0.6-1) ...
Setting up gdal-data (3.4.1+dfsg-1build4) ...
Setting up libasan6:amd64 (11.4.0-1ubuntu1~22.04.3) ...
Setting up libxcb-util1:amd64 (0.4.0-1build2) ...
Setting up libsnappy1v5:amd64 (1.1.8-1build3) ...
Setting up libxcb-xkb1:amd64 (1.14-3ubuntu3) ...
Setting up libxcb-image0:amd64 (0.4.0-2) ...
Setting up libcfitsio9:amd64 (4.0.0-1) ...
Setting up libaom-dev:amd64 (3.3.0-1ubuntu0.1) ...
Setting up unicode-data (14.0.0-1.1) ...
Setting up python3-beniget (0.4.1-2) ...
Setting up libminizip-dev:amd64 (1.1-8build1) ...
Setting up libxsimd-dev:amd64 (7.6.0-2) ...
Setting up python3-decorator (4.4.2-0ubuntu1) ...
Setting up autotools-dev (20220109.1) ...
Setting up libpcre2-32-0:amd64 (10.39-3ubuntu0.1) ...
Setting up libblas3:amd64 (3.10.0-2ubuntu1) ...
update-alternatives: using /usr/lib/x86_64-linux-gnu/blas/libblas.so.3 to provide /usr/lib/x86_64-linux-gnu/libblas.so.3 (libblas.so.3-x86_64-linux-gnu) in auto mode
Setting up python3-packaging (21.3-1) ...
Setting up libxcb-xinerama0:amd64 (1.14-3ubuntu3) ...
Setting up libtirpc-dev:amd64 (1.3.2-2ubuntu0.1) ...
Setting up rpcsvc-proto (1.4.2-0ubuntu6) ...
Setting up emacsen-common (3.0.4) ...
Setting up make (4.3-4.1build1) ...
Setting up libnspr4:amd64 (2:4.35-0ubuntu0.22.04.1) ...
Setting up dh-elpa-helper (2.0.9ubuntu1) ...
Setting up libnotify4:amd64 (0.7.9-3ubuntu5.22.04.1) ...
Setting up aglfn (1.7+git20191031.4036a9c-2) ...
Setting up python3-brotli (1.0.9-2build6) ...
Setting up libraqm0:amd64 (0.7.0-4ubuntu1) ...
Setting up libquadmath0:amd64 (12.3.0-1ubuntu1~22.04.3) ...
Setting up python3-cycler (0.11.0-1) ...
Setting up libimagequant0:amd64 (2.17.0-1) ...
Setting up libxkbcommon-x11-0:amd64 (1.4.0-1) ...
Setting up libssl-dev:amd64 (3.0.2-0ubuntu1.26) ...
Setting up python3-kiwisolver (1.3.2-1build1) ...
Setting up libpng16-16:amd64 (1.6.37-3ubuntu0.6) ...
Setting up libmpc3:amd64 (1.2.1-2build1) ...
Setting up libatomic1:amd64 (12.3.0-1ubuntu1~22.04.3) ...
Setting up libtinyxml2-9:amd64 (9.0.0+dfsg-3) ...
Setting up libtcl8.6:amd64 (8.6.12+dfsg-1build1) ...
Setting up libpython3.10-minimal:amd64 (3.10.12-1~22.04.16) ...
Setting up libjsoncpp25:amd64 (1.9.5-3) ...
Setting up icu-devtools (70.1-2) ...
Setting up liblz4-dev:amd64 (1.9.3-2build2) ...
Setting up libgeos-c1v5:amd64 (3.10.2-1) ...
Setting up unixodbc-common (2.3.9-5ubuntu0.1) ...
Setting up libqhullcpp8.0:amd64 (2020.2-4) ...
Setting up python3-pip (22.0.2+dfsg-1ubuntu0.7) ...
Setting up libtinyxml2-dev:amd64 (9.0.0+dfsg-3) ...
Setting up libqt5core5a:amd64 (5.15.3+dfsg-2ubuntu0.2) ...
Setting up libltdl7:amd64 (2.4.6-15build2) ...
Setting up libqhull-dev:amd64 (2020.2-4) ...
Setting up libdpkg-perl (1.21.1ubuntu2.6) ...
Setting up libgfortran5:amd64 (12.3.0-1ubuntu1~22.04.3) ...
Setting up libmtdev1:amd64 (1.1.6-1build4) ...
Setting up autoconf (2.71-2) ...
Setting up libhdf4-0-alt (4.2.15-4) ...
Setting up libx265-199:amd64 (3.5-2) ...
Setting up liblzma-dev:amd64 (5.2.5-2ubuntu1.1) ...
Setting up libubsan1:amd64 (12.3.0-1ubuntu1~22.04.3) ...
Setting up libgif7:amd64 (5.1.9-2ubuntu0.3) ...
Setting up libodbc2:amd64 (2.3.9-5ubuntu0.1) ...
Setting up liburiparser1:amd64 (0.9.6+dfsg-1) ...
Setting up libpcre2-posix3:amd64 (10.39-3ubuntu0.1) ...
Setting up librttopo1:amd64 (1.1.0-2) ...
Setting up libfreexl1:amd64 (1.0.6-1) ...
Setting up libnsl-dev:amd64 (1.3.0-2build2) ...
Setting up libgif-dev (5.1.9-2ubuntu0.3) ...
Setting up libqt5dbus5:amd64 (5.15.3+dfsg-2ubuntu0.2) ...
Setting up librhash0:amd64 (1.4.2-1ubuntu1) ...
Setting up libcrypt-dev:amd64 (1:4.4.27-1) ...
Setting up libfyba0:amd64 (4.1.1-7) ...
Setting up libjson-perl (4.04000-1) ...
Setting up libkmlbase1:amd64 (1.3.0-9) ...
Setting up libblosc1:amd64 (1.21.1+ds2-2) ...
Setting up libmd4c0:amd64 (0.4.8-1) ...
Setting up libcurl4:amd64 (7.81.0-1ubuntu1.26) ...
Setting up liblua5.4-0:amd64 (5.4.4-1) ...
Setting up libopenjp2-7:amd64 (2.4.0-6ubuntu0.5) ...
Setting up python3-dateutil (2.8.1-6) ...
Setting up libwxbase3.0-0v5:amd64 (3.0.5.1+dfsg-4) ...
Setting up cmake-data (3.22.1-1ubuntu1.22.04.2) ...
Setting up libtiff5:amd64 (4.3.0-6ubuntu0.13) ...
Setting up curl (7.81.0-1ubuntu1.26) ...
Setting up libxss1:amd64 (1:1.2.3-1build2) ...
Setting up libtbb-dev:amd64 (2021.5.0-7ubuntu2) ...
Setting up nlohmann-json3-dev (3.10.5-2) ...
Setting up libjs-jquery (3.6.0+dfsg+~3.5.13-1) ...
Setting up libdav1d5:amd64 (0.9.2-1) ...
Setting up swig4.0 (4.0.2-1ubuntu1) ...
Setting up python3-mpmath (1.2.1-2) ...
Setting up libisl23:amd64 (0.24-2build1) ...
Setting up libde265-0:amd64 (1.0.8-1ubuntu0.3) ...
Setting up libc-dev-bin (2.35-0ubuntu3.14) ...
Setting up python-matplotlib-data (3.5.1-2build1) ...
Setting up libwebpmux3:amd64 (1.2.2-2ubuntu0.22.04.2) ...
Setting up libdeflate-dev:amd64 (1.10-2) ...
Setting up libperlio-gzip-perl (0.19-1build8) ...
Setting up python3-appdirs (1.4.4-2) ...
Setting up libsm6:amd64 (2:1.2.3-1build2) ...
Setting up libevdev2:amd64 (1.12.1+dfsg-1) ...
Setting up libogdi-dev (4.1.0+ds-5) ...
Setting up libxml2:amd64 (2.9.13+dfsg-1ubuntu0.12) ...
Setting up libcc1-0:amd64 (12.3.0-1ubuntu1~22.04.3) ...
Setting up libgudev-1.0-0:amd64 (1:237-2build1) ...
Setting up liblsan0:amd64 (12.3.0-1ubuntu1~22.04.3) ...
Setting up libsz2:amd64 (1.0.6-1) ...
Setting up libitm1:amd64 (12.3.0-1ubuntu1~22.04.3) ...
Setting up libkmlxsd1:amd64 (1.3.0-9) ...
Setting up libtiffxx5:amd64 (4.3.0-6ubuntu0.13) ...
Setting up libjs-underscore (1.13.2~dfsg-2) ...
Setting up libodbccr2:amd64 (2.3.9-5ubuntu0.1) ...
Setting up libwacom-common (2.2.0-1) ...
Setting up libtsan0:amd64 (11.4.0-1ubuntu1~22.04.3) ...
Setting up libkmldom1:amd64 (1.3.0-9) ...
Setting up automake (1:1.16.5-1.3) ...
update-alternatives: using /usr/bin/automake-1.16 to provide /usr/bin/automake (automake) in auto mode
Setting up cpp-11 (11.4.0-1ubuntu1~22.04.3) ...
Setting up python3-sympy (1.9-1) ...
Setting up gnuplot-data (5.4.2+dfsg2-2) ...
Setting up librttopo-dev:amd64 (1.1.0-2) ...
Setting up libcharls-dev:amd64 (2.3.4-1) ...
Setting up libodbcinst2:amd64 (2.3.9-5ubuntu0.1) ...
Setting up liblapack3:amd64 (3.10.0-2ubuntu1) ...
update-alternatives: using /usr/lib/x86_64-linux-gnu/lapack/liblapack.so.3 to provide /usr/lib/x86_64-linux-gnu/liblapack.so.3 (liblapack.so.3-x86_64-linux-gnu) in auto mode
Setting up swig (4.0.2-1ubuntu1) ...
Setting up libcfitsio-dev:amd64 (4.0.0-1) ...
Setting up libopenblas0-pthread:amd64 (0.3.20+ds-1) ...
update-alternatives: using /usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3 to provide /usr/lib/x86_64-linux-gnu/libblas.so.3 (libblas.so.3-x86_64-linux-gnu) in auto mode
update-alternatives: using /usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3 to provide /usr/lib/x86_64-linux-gnu/liblapack.so.3 (liblapack.so.3-x86_64-linux-gnu) in auto mode
update-alternatives: using /usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblas.so.0 to provide /usr/lib/x86_64-linux-gnu/libopenblas.so.0 (libopenblas.so.0-x86_64-linux-gnu) in auto mode
Setting up libkmlengine1:amd64 (1.3.0-9) ...
Setting up libgtest-dev:amd64 (1.11.0-3) ...
Setting up libkmlconvenience1:amd64 (1.3.0-9) ...
Setting up libblosc-dev (1.21.1+ds2-2) ...
Setting up libarchive13:amd64 (3.6.0-1ubuntu1.8) ...
Setting up libwacom9:amd64 (2.2.0-1) ...
Setting up libfreexl-dev:amd64 (1.0.6-1) ...
Setting up libfyba-dev:amd64 (4.1.1-7) ...
Setting up libtk8.6:amd64 (8.6.12-1build1) ...
Setting up libheif1:amd64 (1.12.0-2build1) ...
Setting up libaec-dev:amd64 (1.0.6-1) ...
Setting up libarpack2:amd64 (3.8.0-1) ...
Setting up libsuperlu5:amd64 (5.3.0+dfsg1-2) ...
Setting up libpq-dev (14.24-0ubuntu0.22.04.1) ...
Setting up libnss3:amd64 (2:3.98-0ubuntu0.22.04.4) ...
Setting up libproj22:amd64 (8.2.1-1) ...
Setting up python3.10-minimal (3.10.12-1~22.04.16) ...
Setting up libwxgtk3.0-gtk3-0v5:amd64 (3.0.5.1+dfsg-4) ...
Setting up libqt5network5:amd64 (5.15.3+dfsg-2ubuntu0.2) ...
Setting up dpkg-dev (1.21.1ubuntu2.6) ...
Setting up libgeotiff5:amd64 (1.7.0-2build1) ...
Setting up libinput-bin (1.20.0-1ubuntu0.4) ...
Setting up liburiparser-dev (0.9.6+dfsg-1) ...
Setting up python3-fs (2.4.12-1) ...
Setting up libpython3.10-stdlib:amd64 (3.10.12-1~22.04.16) ...
Setting up libpoppler118:amd64 (22.02.0-2ubuntu0.13) ...
Setting up libltdl-dev:amd64 (2.4.6-15build2) ...
Setting up libwebp-dev:amd64 (1.2.2-2ubuntu0.22.04.2) ...
Setting up libjs-jquery-ui (1.13.1+dfsg-1) ...
Setting up libde265-dev:amd64 (1.0.8-1ubuntu0.3) ...
Setting up libopenjp2-7-dev:amd64 (2.4.0-6ubuntu0.5) ...
Setting up libcurl4-openssl-dev:amd64 (7.81.0-1ubuntu1.26) ...
Setting up libkmlregionator1:amd64 (1.3.0-9) ...
Setting up libgeos-dev (3.10.2-1) ...
Setting up libdav1d-dev:amd64 (0.9.2-1) ...
Setting up libx265-dev:amd64 (3.5-2) ...
Setting up libgd3:amd64 (2.3.0-2ubuntu2.3) ...
Setting up pkg-config (0.29.2-1ubuntu3) ...
Setting up libjs-sphinxdoc (4.3.2-1) ...
Setting up libllvm14:amd64 (1:14.0.0-1ubuntu1.1) ...
Setting up libgcc-11-dev:amd64 (11.4.0-1ubuntu1~22.04.3) ...
Setting up libhdf5-103-1:amd64 (1.10.7+repack-4ubuntu2) ...
Setting up gcc-11 (11.4.0-1ubuntu1~22.04.3) ...
Setting up libopenblas0:amd64 (0.3.20+ds-1) ...
Setting up cpp (4:11.2.0-1ubuntu1) ...
Setting up libxslt1.1:amd64 (1.1.34-4ubuntu0.22.04.5) ...
Setting up libhdf5-cpp-103-1:amd64 (1.10.7+repack-4ubuntu2) ...
Setting up cmake (3.22.1-1ubuntu1.22.04.2) ...
Setting up libc6-dev:amd64 (2.35-0ubuntu3.14) ...
Setting up libicu-dev:amd64 (70.1-2) ...
Setting up unixodbc-dev:amd64 (2.3.9-5ubuntu0.1) ...
Setting up liblbfgsb0:amd64 (3.0+dfsg.3-10) ...
Setting up libhdf5-hl-100:amd64 (1.10.7+repack-4ubuntu2) ...
Setting up libopenblas-pthread-dev:amd64 (0.3.20+ds-1) ...
update-alternatives: using /usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so to provide /usr/lib/x86_64-linux-gnu/libblas.so (libblas.so-x86_64-linux-gnu) in auto mode
update-alternatives: using /usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so to provide /usr/lib/x86_64-linux-gnu/liblapack.so (liblapack.so-x86_64-linux-gnu) in auto mode
update-alternatives: using /usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblas.so to provide /usr/lib/x86_64-linux-gnu/libopenblas.so (libopenblas.so-x86_64-linux-gnu) in auto mode
Setting up libpoppler-dev:amd64 (22.02.0-2ubuntu0.13) ...
Setting up libspatialite7:amd64 (5.0.1-2build2) ...
Setting up libinput10:amd64 (1.20.0-1ubuntu0.4) ...
Setting up libpython3.10:amd64 (3.10.12-1~22.04.16) ...
Setting up libjpeg-turbo8-dev:amd64 (2.1.2-0ubuntu1) ...
Setting up tk8.6-blt2.5 (2.5.3+dfsg-4.1build2) ...
Setting up libarmadillo10 (1:10.8.2+dfsg-1) ...
Setting up libarpack2-dev:amd64 (3.8.0-1) ...
Setting up python3.10 (3.10.12-1~22.04.16) ...
Setting up libpcre2-dev:amd64 (10.39-3ubuntu0.1) ...
Setting up blt (2.5.3+dfsg-4.1build2) ...
Setting up libpoppler-private-dev:amd64 (22.02.0-2ubuntu0.13) ...
Setting up libqt5gui5:amd64 (5.15.3+dfsg-2ubuntu0.2) ...
Setting up libclang1-14 (1:14.0.0-1ubuntu1.1) ...
Setting up libheif-dev:amd64 (1.12.0-2build1) ...
Setting up python3-tk:amd64 (3.10.8-1~22.04) ...
Setting up libqt5widgets5:amd64 (5.15.3+dfsg-2ubuntu0.2) ...
Setting up gcc (4:11.2.0-1ubuntu1) ...
Setting up libqt5printsupport5:amd64 (5.15.3+dfsg-2ubuntu0.2) ...
Setting up libopenblas-dev:amd64 (0.3.20+ds-1) ...
Setting up libxml2-dev:amd64 (2.9.13+dfsg-1ubuntu0.12) ...
Setting up libhdf5-hl-cpp-100:amd64 (1.10.7+repack-4ubuntu2) ...
Setting up libexpat1-dev:amd64 (2.4.7-1ubuntu0.7) ...
Setting up libsqlite3-dev:amd64 (3.37.2-2ubuntu0.7) ...
Setting up libxerces-c-dev:amd64 (3.2.3+debian-3ubuntu0.1) ...
Setting up libeigen3-dev (3.4.0-2ubuntu2) ...
Setting up libhdf5-fortran-102:amd64 (1.10.7+repack-4ubuntu2) ...
Setting up libclang-cpp14 (1:14.0.0-1ubuntu1.1) ...
Setting up python3-numpy (1:1.21.5-1ubuntu22.04.1) ...
Setting up libstdc++-11-dev:amd64 (11.4.0-1ubuntu1~22.04.3) ...
Setting up zlib1g-dev:amd64 (1:1.2.11.dfsg-2ubuntu9.2) ...
Setting up libnetcdf19:amd64 (1:4.8.1-1) ...
Setting up python3-lxml:amd64 (4.8.0-1build1) ...
Setting up libhdf5-hl-fortran-100:amd64 (1.10.7+repack-4ubuntu2) ...
Setting up libjpeg8-dev:amd64 (8c-2ubuntu10) ...
Setting up libsuperlu-dev:amd64 (5.3.0+dfsg1-2) ...
Setting up libmysqlclient-dev (8.0.46-0ubuntu0.22.04.3) ...
Setting up default-libmysqlclient-dev:amd64 (1.0.8) ...
Setting up libboost1.74-dev:amd64 (1.74.0-14ubuntu3) ...
Setting up python3.10-venv (3.10.12-1~22.04.16) ...
Setting up g++-11 (11.4.0-1ubuntu1~22.04.3) ...
Setting up libpng-dev:amd64 (1.6.37-3ubuntu0.6) ...
Setting up libqt5svg5:amd64 (5.15.3-1) ...
Setting up libjpeg-dev:amd64 (8c-2ubuntu10) ...
Setting up lcov (1.15-1) ...
Setting up gnuplot-qt (5.4.2+dfsg2-2) ...
update-alternatives: using /usr/bin/gnuplot-qt to provide /usr/bin/gnuplot (gnuplot) in auto mode
Setting up doxygen (1.9.1-2ubuntu2) ...
Setting up python3-venv (3.10.6-1~22.04.1) ...
Setting up libgdal30 (3.4.1+dfsg-1build4) ...
Setting up libtiff-dev:amd64 (4.3.0-6ubuntu0.13) ...
Setting up libhdf5-dev (1.10.7+repack-4ubuntu2) ...
update-alternatives: using /usr/lib/x86_64-linux-gnu/pkgconfig/hdf5-serial.pc to provide /usr/lib/x86_64-linux-gnu/pkgconfig/hdf5.pc (hdf5.pc) in auto mode
Setting up libproj-dev:amd64 (8.2.1-1) ...
Setting up libpython3.10-dev:amd64 (3.10.12-1~22.04.16) ...
Setting up libnetcdf-dev (1:4.8.1-1) ...
Setting up libspatialite-dev:amd64 (5.0.1-2build2) ...
Setting up python3.10-dev (3.10.12-1~22.04.16) ...
Setting up g++ (4:11.2.0-1ubuntu1) ...
update-alternatives: using /usr/bin/g++ to provide /usr/bin/c++ (c++) in auto mode
Setting up build-essential (12.9ubuntu3) ...
Setting up libboost-dev:amd64 (1.74.0.3ubuntu7) ...
Setting up gnuplot (5.4.2+dfsg2-2) ...
Setting up libkml-dev:amd64 (1.3.0-9) ...
Setting up libpython3-dev:amd64 (3.10.6-1~22.04.1) ...
Setting up libgeotiff-dev:amd64 (1.7.0-2build1) ...
Setting up libarmadillo-dev (1:10.8.2+dfsg-1) ...
Setting up python3-dev (3.10.6-1~22.04.1) ...
Setting up libhdf4-alt-dev (4.2.15-4) ...
Setting up libgdal-dev (3.4.1+dfsg-1build4) ...
Setting up python3-pythran (0.10.0+ds2-1) ...
Setting up python3-scipy (1.8.0-1exp2ubuntu1) ...
Setting up python3-pil.imagetk:amd64 (9.0.1-1ubuntu0.4) ...
Setting up python3-ufolib2 (0.13.1+dfsg1-1) ...
Setting up python3-fonttools (4.29.1-2build1) ...
Setting up python3-pil:amd64 (9.0.1-1ubuntu0.4) ...
Setting up python3-matplotlib (3.5.1-2build1) ...
Processing triggers for libc-bin (2.35-0ubuntu3.13) ...
Processing triggers for man-db (2.10.2-1) ...
Processing triggers for udev (249.11-0ubuntu3.17) ...
Processing triggers for install-info (6.8-4build1) ...
Processing triggers for fontconfig (2.13.1-4.2ubuntu5) ...
Cloning into '/root/Fields2Cover'...
From https://github.com/Fields2Cover/Fields2Cover
 * branch            3613525c241538fa9fd9df3e1209ae8184627958 -> FETCH_HEAD
Note: switching to '3613525c241538fa9fd9df3e1209ae8184627958'.

You are in 'detached HEAD' state. You can look around, make experimental
changes and commit them, and you can discard any commits you make in this
state without impacting any branches by switching back to a branch.

If you want to create a new branch to retain commits you create, you may
do so (now or later) by using -c with the switch command. Example:

  git switch -c <new-branch-name>

Or undo this operation with:

  git switch -

Turn off this advice by setting config variable advice.detachedHead to false

HEAD is now at 3613525 Adjust dubins_curves_cc.cpp to match style and minimize diff
  [02_f2c] 构建（Release + BUILD_PYTHON）。OR-Tools 首次要编译，预计 20-40 分钟。
-- The CXX compiler identification is GNU 11.4.0
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/c++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Found TinyXML2: /usr/lib/x86_64-linux-gnu/libtinyxml2.so  
-- Looking for C++ include pthread.h
-- Looking for C++ include pthread.h - found
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD - Success
-- Found Threads: TRUE  
-- Found Gnuplot: /usr/bin/gnuplot (found version "5.4.2") 
-- Found GDAL: /usr/lib/libgdal.so (found suitable version "3.4.1", minimum required is "3.0") 
-- or-tools -- Downloading and installing from release tarball
-- Target architecture is AMD64
-- Found ZLIB: /root/Fields2Cover/build/_deps/ortools-src/lib/libz.a (found version "1.2.13") 
-- Found re2: /root/Fields2Cover/build/_deps/ortools-src/lib/cmake/re2/re2Config.cmake (found version "11.0.0") 
-- Found Clp: /root/Fields2Cover/build/_deps/ortools-src/lib/cmake/Clp/ClpConfig.cmake (found version "1.17.7") 
-- Found Cbc: /root/Fields2Cover/build/_deps/ortools-src/lib/cmake/Cbc/CbcConfig.cmake (found version "2.10.7") 
-- Found SCIP: /root/Fields2Cover/build/_deps/ortools-src/lib/cmake/scip/scip-config.cmake (found version "8.1.0") 
-- The C compiler identification is GNU 11.4.0
-- Detecting C compiler ABI info
-- Detecting C compiler ABI info - done
-- Check for working C compiler: /usr/bin/cc - skipped
-- Detecting C compile features
-- Detecting C compile features - done
-- Found Eigen3: /usr/share/eigen3/cmake/Eigen3Config.cmake (found version "3.4.0") 
-- Found PkgConfig: /usr/bin/pkg-config (found version "0.29.2") 
-- Found JPEG: /usr/lib/x86_64-linux-gnu/libjpeg.so (found version "80") 
-- Found TIFF: /usr/lib/x86_64-linux-gnu/libtiff.so (found version "4.3.0")  
-- Found PNG: /usr/lib/x86_64-linux-gnu/libpng.so (found version "1.6.37") 
-- Looking for sgemm_
-- Looking for sgemm_ - not found
-- Looking for sgemm_
-- Looking for sgemm_ - found
-- Found BLAS: /usr/lib/x86_64-linux-gnu/libopenblas.so  
-- Looking for cheev_
-- Looking for cheev_ - found
-- Found LAPACK: /usr/lib/x86_64-linux-gnu/libopenblas.so;-lm;-ldl  
-- Could NOT find FFTW (missing: FFTW_INCLUDE_DIRS) 
-- Performing Test COMPILER_HAS_HIDDEN_VISIBILITY
-- Performing Test COMPILER_HAS_HIDDEN_VISIBILITY - Success
-- Performing Test COMPILER_HAS_HIDDEN_INLINE_VISIBILITY
-- Performing Test COMPILER_HAS_HIDDEN_INLINE_VISIBILITY - Success
-- Performing Test COMPILER_HAS_DEPRECATED_ATTR
-- Performing Test COMPILER_HAS_DEPRECATED_ATTR - Success
Setting matplotplusplus compiler options
-- Looking for __fbufsize
-- Looking for __fbufsize - found
-- Using the multi-header code from /root/Fields2Cover/build/_deps/json-src/include/
-- Found SWIG: /usr/bin/swig4.0 (found suitable version "4.0.2", minimum required is "4.0")  
-- Found Python: /usr/bin/python3.10 (found version "3.10.12") found components: Interpreter Development Development.Module Development.Embed 
-- Configuring done
-- Generating done
-- Build files have been written to: /root/Fields2Cover/build
Scanning dependencies of target fields2cover_python_swig_compilation
[  4%] Swig compile ../Fields2Cover.i for python
[ 19%] Linking CXX static library libnodesoup.a
[ 19%] Built target nodesoup
[ 38%] Linking CXX shared library libsteering_functions.so
[ 41%] Built target steering_functions
[ 47%] Built target fields2cover_python_swig_compilation
[ 47%] Linking CXX shared library libmatplot.so
[ 47%] Built target matplot
[ 87%] Linking CXX shared library libFields2Cover.so
[ 87%] Built target Fields2Cover
[ 94%] Linking CXX executable 3_headland_generator_tutorial
[ 94%] Linking CXX executable 4_swath_generator_tutorial
[ 95%] Linking CXX executable quick_start
[ 96%] Linking CXX executable 7_decomposition_tutorial
[ 97%] Linking CXX executable 1_basic_types_tutorial
[ 98%] Linking CXX executable 8_complete_flow
[ 99%] Linking CXX executable 6_path_planning_tutorial
[ 99%] Linking CXX executable 2_objective_functions_tutorial
[100%] Linking CXX executable 5_route_planning_tutorial
[100%] Built target 3_headland_generator_tutorial
[100%] Built target 4_swath_generator_tutorial
[100%] Built target quick_start
[100%] Built target 7_decomposition_tutorial
[100%] Built target 8_complete_flow
[100%] Built target 6_path_planning_tutorial
[100%] Built target 1_basic_types_tutorial
[100%] Built target 2_objective_functions_tutorial
[100%] Built target 5_route_planning_tutorial
[100%] Linking CXX shared module _fields2cover_python.so
[100%] Built target fields2cover_python
-- Install configuration: "Release"
-- Up-to-date: /usr/local
-- Up-to-date: /usr/local/lib
-- Installing: /usr/local/lib/libabsl_time_zone.a
-- Installing: /usr/local/lib/libabsl_log_entry.a
-- Installing: /usr/local/lib/libabsl_flags_reflection.a
-- Installing: /usr/local/lib/libortools_flatzinc.so
-- Installing: /usr/local/lib/libabsl_crc_internal.a
-- Installing: /usr/local/lib/libortools.so
-- Installing: /usr/local/lib/libabsl_kernel_timeout_internal.a
-- Installing: /usr/local/lib/libabsl_random_distributions.a
-- Installing: /usr/local/lib/libabsl_log_initialize.a
-- Installing: /usr/local/lib/libabsl_exponential_biased.a
-- Installing: /usr/local/lib/libabsl_spinlock_wait.a
-- Installing: /usr/local/lib/libabsl_log_sink.a
-- Installing: /usr/local/lib/libabsl_throw_delegate.a
-- Installing: /usr/local/lib/cmake
-- Installing: /usr/local/lib/cmake/CoinUtils
-- Installing: /usr/local/lib/cmake/CoinUtils/CoinUtilsTargets.cmake
-- Installing: /usr/local/lib/cmake/CoinUtils/CoinUtilsTargets-release.cmake
-- Installing: /usr/local/lib/cmake/CoinUtils/CoinUtilsConfigVersion.cmake
-- Installing: /usr/local/lib/cmake/CoinUtils/CoinUtilsConfig.cmake
-- Installing: /usr/local/lib/cmake/Cbc
-- Installing: /usr/local/lib/cmake/Cbc/CbcTargets-release.cmake
-- Installing: /usr/local/lib/cmake/Cbc/CbcConfigVersion.cmake
-- Installing: /usr/local/lib/cmake/Cbc/CbcConfig.cmake
-- Installing: /usr/local/lib/cmake/Cbc/CbcTargets.cmake
-- Installing: /usr/local/lib/cmake/scip
-- Installing: /usr/local/lib/cmake/scip/scip-config.cmake
-- Installing: /usr/local/lib/cmake/scip/scip-targets.cmake
-- Installing: /usr/local/lib/cmake/scip/scip-targets-release.cmake
-- Installing: /usr/local/lib/cmake/scip/scip-config-version.cmake
-- Installing: /usr/local/lib/cmake/Cgl
-- Installing: /usr/local/lib/cmake/Cgl/CglTargets.cmake
-- Installing: /usr/local/lib/cmake/Cgl/CglTargets-release.cmake
-- Installing: /usr/local/lib/cmake/Cgl/CglConfig.cmake
-- Installing: /usr/local/lib/cmake/Cgl/CglConfigVersion.cmake
-- Installing: /usr/local/lib/cmake/absl
-- Installing: /usr/local/lib/cmake/absl/abslTargets-release.cmake
-- Installing: /usr/local/lib/cmake/absl/abslConfig.cmake
-- Installing: /usr/local/lib/cmake/absl/abslConfigVersion.cmake
-- Installing: /usr/local/lib/cmake/absl/abslTargets.cmake
-- Installing: /usr/local/lib/cmake/Clp
-- Installing: /usr/local/lib/cmake/Clp/ClpTargets-release.cmake
-- Installing: /usr/local/lib/cmake/Clp/ClpConfig.cmake
-- Installing: /usr/local/lib/cmake/Clp/ClpConfigVersion.cmake
-- Installing: /usr/local/lib/cmake/Clp/ClpTargets.cmake
-- Installing: /usr/local/lib/cmake/Osi
-- Installing: /usr/local/lib/cmake/Osi/OsiConfig.cmake
-- Installing: /usr/local/lib/cmake/Osi/OsiTargets-release.cmake
-- Installing: /usr/local/lib/cmake/Osi/OsiTargets.cmake
-- Installing: /usr/local/lib/cmake/Osi/OsiConfigVersion.cmake
-- Installing: /usr/local/lib/cmake/protobuf
-- Installing: /usr/local/lib/cmake/protobuf/protobuf-config.cmake
-- Installing: /usr/local/lib/cmake/protobuf/protobuf-module.cmake
-- Installing: /usr/local/lib/cmake/protobuf/protobuf-targets-release.cmake
-- Installing: /usr/local/lib/cmake/protobuf/protobuf-options.cmake
-- Installing: /usr/local/lib/cmake/protobuf/protobuf-generate.cmake
-- Installing: /usr/local/lib/cmake/protobuf/protobuf-config-version.cmake
-- Installing: /usr/local/lib/cmake/protobuf/protobuf-targets.cmake
-- Installing: /usr/local/lib/cmake/re2
-- Installing: /usr/local/lib/cmake/re2/re2ConfigVersion.cmake
-- Installing: /usr/local/lib/cmake/re2/re2Targets-release.cmake
-- Installing: /usr/local/lib/cmake/re2/re2Config.cmake
-- Installing: /usr/local/lib/cmake/re2/re2Targets.cmake
-- Installing: /usr/local/lib/cmake/ortools
-- Installing: /usr/local/lib/cmake/ortools/ortoolsConfig.cmake
-- Installing: /usr/local/lib/cmake/ortools/ortoolsTargets.cmake
-- Installing: /usr/local/lib/cmake/ortools/ortoolsConfigVersion.cmake
-- Installing: /usr/local/lib/cmake/ortools/ortoolsTargets-release.cmake
-- Installing: /usr/local/lib/cmake/ortools/modules
-- Installing: /usr/local/lib/cmake/ortools/modules/FindEigen3.cmake
-- Installing: /usr/local/lib/cmake/ortools/modules/FindCbc.cmake
-- Installing: /usr/local/lib/cmake/ortools/modules/Findre2.cmake
-- Installing: /usr/local/lib/cmake/ortools/modules/FindSCIP.cmake
-- Installing: /usr/local/lib/cmake/ortools/modules/FindClp.cmake
-- Installing: /usr/local/lib/cmake/utf8_range
-- Installing: /usr/local/lib/cmake/utf8_range/utf8_range-config.cmake
-- Installing: /usr/local/lib/cmake/utf8_range/utf8_range-targets.cmake
-- Installing: /usr/local/lib/cmake/utf8_range/utf8_range-targets-release.cmake
-- Installing: /usr/local/lib/cmake/ZLIB
-- Installing: /usr/local/lib/cmake/ZLIB/ZLIBTargets.cmake
-- Installing: /usr/local/lib/cmake/ZLIB/ZLIBTargets-release.cmake
-- Installing: /usr/local/lib/cmake/ZLIB/ZLIBConfigVersion.cmake
-- Installing: /usr/local/lib/cmake/ZLIB/ZLIBConfig.cmake
-- Installing: /usr/local/lib/libabsl_log_internal_conditions.a
-- Installing: /usr/local/lib/libabsl_vlog_config_internal.a
-- Installing: /usr/local/lib/libabsl_flags_internal.a
-- Installing: /usr/local/lib/libabsl_random_internal_randen_hwaes_impl.a
-- Installing: /usr/local/lib/libabsl_cordz_info.a
-- Installing: /usr/local/lib/libabsl_random_internal_randen_hwaes.a
-- Installing: /usr/local/lib/libabsl_random_internal_randen.a
-- Installing: /usr/local/lib/libre2.a
-- Installing: /usr/local/lib/libabsl_flags_commandlineflag.a
-- Installing: /usr/local/lib/libabsl_log_globals.a
-- Installing: /usr/local/lib/libabsl_leak_check.a
-- Installing: /usr/local/lib/libabsl_flags_usage.a
-- Installing: /usr/local/lib/libabsl_cordz_functions.a
-- Installing: /usr/local/lib/libabsl_log_internal_format.a
-- Installing: /usr/local/lib/libabsl_raw_logging_internal.a
-- Installing: /usr/local/lib/libabsl_crc32c.a
-- Installing: /usr/local/lib/libabsl_cord_internal.a
-- Installing: /usr/local/lib/libabsl_demangle_internal.a
-- Installing: /usr/local/lib/libabsl_cordz_handle.a
-- Installing: /usr/local/lib/libabsl_log_internal_nullguard.a
-- Installing: /usr/local/lib/libabsl_flags_program_name.a
-- Installing: /usr/local/lib/libCbcSolver.a
-- Installing: /usr/local/lib/pkgconfig
-- Installing: /usr/local/lib/pkgconfig/absl_vlog_is_on.pc
-- Installing: /usr/local/lib/pkgconfig/absl_bits.pc
-- Installing: /usr/local/lib/pkgconfig/absl_statusor.pc
-- Installing: /usr/local/lib/pkgconfig/absl_die_if_null.pc
-- Installing: /usr/local/lib/pkgconfig/absl_flags_parse.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_randen_slow.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_fastmath.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_generate_real.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_internal_check_impl.pc
-- Installing: /usr/local/lib/pkgconfig/absl_base.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_distribution_caller.pc
-- Installing: /usr/local/lib/pkgconfig/absl_periodic_sampler.pc
-- Installing: /usr/local/lib/pkgconfig/absl_bad_variant_access.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_fast_uniform_bits.pc
-- Installing: /usr/local/lib/pkgconfig/absl_cordz_update_tracker.pc
-- Installing: /usr/local/lib/pkgconfig/absl_flags_marshalling.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_pool_urbg.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_sink.pc
-- Installing: /usr/local/lib/pkgconfig/absl_flags.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_seed_gen_exception.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_nonsecure_base.pc
-- Installing: /usr/local/lib/pkgconfig/absl_stacktrace.pc
-- Installing: /usr/local/lib/pkgconfig/absl_algorithm_container.pc
-- Installing: /usr/local/lib/pkgconfig/absl_flags_private_handle_accessor.pc
-- Installing: /usr/local/lib/pkgconfig/absl_flags_usage_internal.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_randen.pc
-- Installing: /usr/local/lib/pkgconfig/absl_civil_time.pc
-- Installing: /usr/local/lib/pkgconfig/absl_compare.pc
-- Installing: /usr/local/lib/pkgconfig/absl_prefetch.pc
-- Installing: /usr/local/lib/pkgconfig/absl_absl_check.pc
-- Installing: /usr/local/lib/pkgconfig/absl_fast_type_id.pc
-- Installing: /usr/local/lib/pkgconfig/absl_vlog_config_internal.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_sink_registry.pc
-- Installing: /usr/local/lib/pkgconfig/absl_numeric.pc
-- Installing: /usr/local/lib/pkgconfig/absl_time.pc
-- Installing: /usr/local/lib/pkgconfig/absl_flags_config.pc
-- Installing: /usr/local/lib/pkgconfig/absl_no_destructor.pc
-- Installing: /usr/local/lib/pkgconfig/absl_hashtable_debug_hooks.pc
-- Installing: /usr/local/lib/pkgconfig/absl_span.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_internal_conditions.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_bit_gen_ref.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_uniform_helper.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_distribution_test_util.pc
-- Installing: /usr/local/lib/pkgconfig/absl_container_common.pc
-- Installing: /usr/local/lib/pkgconfig/utf8_range.pc
-- Installing: /usr/local/lib/pkgconfig/absl_config.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_severity.pc
-- Installing: /usr/local/lib/pkgconfig/absl_memory.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_internal_structured.pc
-- Installing: /usr/local/lib/pkgconfig/absl_city.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_seed_material.pc
-- Installing: /usr/local/lib/pkgconfig/absl_leak_check.pc
-- Installing: /usr/local/lib/pkgconfig/absl_node_slot_policy.pc
-- Installing: /usr/local/lib/pkgconfig/absl_str_format_internal.pc
-- Installing: /usr/local/lib/pkgconfig/absl_hash_function_defaults.pc
-- Installing: /usr/local/lib/pkgconfig/absl_non_temporal_memcpy.pc
-- Installing: /usr/local/lib/pkgconfig/absl_variant.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_internal_voidify.pc
-- Installing: /usr/local/lib/pkgconfig/absl_pretty_function.pc
-- Installing: /usr/local/lib/pkgconfig/absl_cordz_update_scope.pc
-- Installing: /usr/local/lib/pkgconfig/absl_cleanup_internal.pc
-- Installing: /usr/local/lib/pkgconfig/absl_synchronization.pc
-- Installing: /usr/local/lib/pkgconfig/absl_optional.pc
-- Installing: /usr/local/lib/pkgconfig/re2.pc
-- Installing: /usr/local/lib/pkgconfig/absl_has_ostream_operator.pc
-- Installing: /usr/local/lib/pkgconfig/absl_flat_hash_map.pc
-- Installing: /usr/local/lib/pkgconfig/absl_type_traits.pc
-- Installing: /usr/local/lib/pkgconfig/absl_flags_commandlineflag_internal.pc
-- Installing: /usr/local/lib/pkgconfig/absl_any_invocable.pc
-- Installing: /usr/local/lib/pkgconfig/absl_core_headers.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_distributions.pc
-- Installing: /usr/local/lib/pkgconfig/absl_hashtablez_sampler.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_iostream_state_saver.pc
-- Installing: /usr/local/lib/pkgconfig/absl_hashtable_debug.pc
-- Installing: /usr/local/lib/pkgconfig/absl_failure_signal_handler.pc
-- Installing: /usr/local/lib/pkgconfig/absl_cordz_functions.pc
-- Installing: /usr/local/lib/pkgconfig/absl_flags_commandlineflag.pc
-- Installing: /usr/local/lib/pkgconfig/absl_charset.pc
-- Installing: /usr/local/lib/pkgconfig/absl_examine_stack.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_random.pc
-- Installing: /usr/local/lib/pkgconfig/absl_exponential_biased.pc
-- Installing: /usr/local/lib/pkgconfig/absl_flags_usage.pc
-- Installing: /usr/local/lib/pkgconfig/absl_strings_internal.pc
-- Installing: /usr/local/lib/pkgconfig/absl_endian.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_internal_append_truncated.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_internal_check_op.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_flags.pc
-- Installing: /usr/local/lib/pkgconfig/absl_overload.pc
-- Installing: /usr/local/lib/pkgconfig/absl_debugging_internal.pc
-- Installing: /usr/local/lib/pkgconfig/absl_raw_hash_set.pc
-- Installing: /usr/local/lib/pkgconfig/absl_cord_internal.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_pcg_engine.pc
-- Installing: /usr/local/lib/pkgconfig/absl_function_ref.pc
-- Installing: /usr/local/lib/pkgconfig/absl_node_hash_map.pc
-- Installing: /usr/local/lib/pkgconfig/absl_crc_internal.pc
-- Installing: /usr/local/lib/pkgconfig/absl_malloc_internal.pc
-- Installing: /usr/local/lib/pkgconfig/absl_dynamic_annotations.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_internal_message.pc
-- Installing: /usr/local/lib/pkgconfig/absl_graphcycles_internal.pc
-- Installing: /usr/local/lib/pkgconfig/absl_raw_logging_internal.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_internal_strip.pc
-- Installing: /usr/local/lib/pkgconfig/absl_hash.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_internal_format.pc
-- Installing: /usr/local/lib/pkgconfig/absl_cleanup.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_internal_flags.pc
-- Installing: /usr/local/lib/pkgconfig/absl_cordz_statistics.pc
-- Installing: /usr/local/lib/pkgconfig/absl_flags_path_util.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_randen_hwaes.pc
-- Installing: /usr/local/lib/pkgconfig/absl_kernel_timeout_internal.pc
-- Installing: /usr/local/lib/pkgconfig/absl_spinlock_wait.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_internal_config.pc
-- Installing: /usr/local/lib/pkgconfig/absl_crc_cord_state.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_internal_nullstream.pc
-- Installing: /usr/local/lib/pkgconfig/absl_if_constexpr.pc
-- Installing: /usr/local/lib/pkgconfig/absl_string_view.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_internal_globals.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log.pc
-- Installing: /usr/local/lib/pkgconfig/absl_errno_saver.pc
-- Installing: /usr/local/lib/pkgconfig/absl_btree.pc
-- Installing: /usr/local/lib/pkgconfig/absl_flags_reflection.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_internal_log_sink_set.pc
-- Installing: /usr/local/lib/pkgconfig/absl_cordz_info.pc
-- Installing: /usr/local/lib/pkgconfig/absl_nullability.pc
-- Installing: /usr/local/lib/pkgconfig/absl_cordz_sample_token.pc
-- Installing: /usr/local/lib/pkgconfig/absl_strings.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_internal_log_impl.pc
-- Installing: /usr/local/lib/pkgconfig/absl_throw_delegate.pc
-- Installing: /usr/local/lib/pkgconfig/absl_str_format.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_globals.pc
-- Installing: /usr/local/lib/pkgconfig/absl_bind_front.pc
-- Installing: /usr/local/lib/pkgconfig/absl_bad_optional_access.pc
-- Installing: /usr/local/lib/pkgconfig/absl_cord.pc
-- Installing: /usr/local/lib/pkgconfig/absl_sample_recorder.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_wide_multiply.pc
-- Installing: /usr/local/lib/pkgconfig/absl_utility.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_traits.pc
-- Installing: /usr/local/lib/pkgconfig/absl_cordz_handle.pc
-- Installing: /usr/local/lib/pkgconfig/absl_scoped_set_env.pc
-- Installing: /usr/local/lib/pkgconfig/absl_time_zone.pc
-- Installing: /usr/local/lib/pkgconfig/absl_fixed_array.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_randen_hwaes_impl.pc
-- Installing: /usr/local/lib/pkgconfig/absl_bad_any_cast_impl.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_internal_nullguard.pc
-- Installing: /usr/local/lib/pkgconfig/absl_common_policy_traits.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_seed_sequences.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_salted_seed_seq.pc
-- Installing: /usr/local/lib/pkgconfig/absl_flags_program_name.pc
-- Installing: /usr/local/lib/pkgconfig/absl_check.pc
-- Installing: /usr/local/lib/pkgconfig/absl_int128.pc
-- Installing: /usr/local/lib/pkgconfig/absl_node_hash_set.pc
-- Installing: /usr/local/lib/pkgconfig/absl_algorithm.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_internal_fnmatch.pc
-- Installing: /usr/local/lib/pkgconfig/absl_crc32c.pc
-- Installing: /usr/local/lib/pkgconfig/absl_debugging.pc
-- Installing: /usr/local/lib/pkgconfig/absl_crc_cpu_detect.pc
-- Installing: /usr/local/lib/pkgconfig/absl_flags_internal.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_randen_engine.pc
-- Installing: /usr/local/lib/pkgconfig/protobuf-lite.pc
-- Installing: /usr/local/lib/pkgconfig/absl_layout.pc
-- Installing: /usr/local/lib/pkgconfig/absl_inlined_vector_internal.pc
-- Installing: /usr/local/lib/pkgconfig/absl_flat_hash_set.pc
-- Installing: /usr/local/lib/pkgconfig/absl_absl_vlog_is_on.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_entry.pc
-- Installing: /usr/local/lib/pkgconfig/absl_low_level_hash.pc
-- Installing: /usr/local/lib/pkgconfig/absl_demangle_internal.pc
-- Installing: /usr/local/lib/pkgconfig/absl_hash_policy_traits.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_initialize.pc
-- Installing: /usr/local/lib/pkgconfig/absl_any.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_mock_helpers.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_structured.pc
-- Installing: /usr/local/lib/pkgconfig/absl_symbolize.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_internal_proto.pc
-- Installing: /usr/local/lib/pkgconfig/protobuf.pc
-- Installing: /usr/local/lib/pkgconfig/absl_strerror.pc
-- Installing: /usr/local/lib/pkgconfig/absl_raw_hash_map.pc
-- Installing: /usr/local/lib/pkgconfig/absl_non_temporal_arm_intrinsics.pc
-- Installing: /usr/local/lib/pkgconfig/absl_log_streamer.pc
-- Installing: /usr/local/lib/pkgconfig/absl_status.pc
-- Installing: /usr/local/lib/pkgconfig/absl_atomic_hook.pc
-- Installing: /usr/local/lib/pkgconfig/absl_random_internal_platform.pc
-- Installing: /usr/local/lib/pkgconfig/absl_absl_log.pc
-- Installing: /usr/local/lib/pkgconfig/absl_bad_any_cast.pc
-- Installing: /usr/local/lib/pkgconfig/absl_container_memory.pc
-- Installing: /usr/local/lib/pkgconfig/absl_numeric_representation.pc
-- Installing: /usr/local/lib/pkgconfig/absl_meta.pc
-- Installing: /usr/local/lib/pkgconfig/absl_base_internal.pc
-- Installing: /usr/local/lib/pkgconfig/absl_compressed_tuple.pc
-- Installing: /usr/local/lib/pkgconfig/absl_inlined_vector.pc
-- Installing: /usr/local/lib/libabsl_strerror.a
-- Installing: /usr/local/lib/libabsl_random_internal_seed_material.a
-- Installing: /usr/local/lib/libabsl_random_internal_randen_slow.a
-- Installing: /usr/local/lib/libabsl_status.a
-- Installing: /usr/local/lib/libabsl_bad_variant_access.a
-- Installing: /usr/local/lib/libabsl_str_format_internal.a
-- Installing: /usr/local/lib/libabsl_cord.a
-- Installing: /usr/local/lib/libabsl_log_internal_fnmatch.a
-- Installing: /usr/local/lib/libabsl_log_internal_message.a
-- Installing: /usr/local/lib/libOsiClp.a
-- Installing: /usr/local/lib/libCoinUtils.a
-- Installing: /usr/local/lib/libabsl_log_internal_check_op.a
-- Installing: /usr/local/lib/libabsl_bad_any_cast_impl.a
-- Installing: /usr/local/lib/libutf8_range.a
-- Installing: /usr/local/lib/libabsl_flags_parse.a
-- Installing: /usr/local/lib/libabsl_random_seed_gen_exception.a
-- Installing: /usr/local/lib/libabsl_base.a
-- Installing: /usr/local/lib/libabsl_low_level_hash.a
-- Installing: /usr/local/lib/libabsl_random_seed_sequences.a
-- Installing: /usr/local/lib/libutf8_validity.a
-- Installing: /usr/local/lib/libabsl_log_internal_globals.a
-- Installing: /usr/local/lib/libabsl_malloc_internal.a
-- Installing: /usr/local/lib/libCbc.a
-- Installing: /usr/local/lib/libabsl_flags_marshalling.a
-- Installing: /usr/local/lib/libabsl_string_view.a
-- Installing: /usr/local/lib/libabsl_log_internal_log_sink_set.a
-- Installing: /usr/local/lib/libortools_flatzinc.so.9
-- Installing: /usr/local/lib/libOsi.a
-- Installing: /usr/local/lib/libabsl_random_internal_distribution_test_util.a
-- Installing: /usr/local/lib/libabsl_random_internal_pool_urbg.a
-- Installing: /usr/local/lib/libprotoc.a
-- Installing: /usr/local/lib/libabsl_strings_internal.a
-- Installing: /usr/local/lib/libabsl_city.a
-- Installing: /usr/local/lib/libCgl.a
-- Installing: /usr/local/lib/libabsl_cordz_sample_token.a
-- Installing: /usr/local/lib/libabsl_die_if_null.a
-- Installing: /usr/local/lib/libabsl_int128.a
-- Installing: /usr/local/lib/libortools_flatzinc.so.9.9.3963
-- Installing: /usr/local/lib/libabsl_raw_hash_set.a
-- Installing: /usr/local/lib/libz.a
-- Installing: /usr/local/lib/libabsl_civil_time.a
-- Installing: /usr/local/lib/libscip.a
-- Installing: /usr/local/lib/libOsiCbc.a
-- Installing: /usr/local/lib/libabsl_log_flags.a
-- Installing: /usr/local/lib/libabsl_time.a
-- Installing: /usr/local/lib/libabsl_symbolize.a
-- Installing: /usr/local/lib/libprotobuf-lite.a
-- Installing: /usr/local/lib/libabsl_flags_config.a
-- Installing: /usr/local/lib/libortools.so.9.9.3963
-- Installing: /usr/local/lib/libabsl_log_severity.a
-- Installing: /usr/local/lib/libabsl_failure_signal_handler.a
-- Installing: /usr/local/lib/libabsl_crc_cord_state.a
-- Installing: /usr/local/lib/libabsl_log_internal_proto.a
-- Installing: /usr/local/lib/libortools.so.9
-- Installing: /usr/local/lib/libabsl_strings.a
-- Installing: /usr/local/lib/libprotobuf.a
-- Installing: /usr/local/lib/libabsl_hashtablez_sampler.a
-- Installing: /usr/local/lib/libabsl_scoped_set_env.a
-- Installing: /usr/local/lib/libabsl_synchronization.a
-- Installing: /usr/local/lib/libabsl_debugging_internal.a
-- Installing: /usr/local/lib/libabsl_stacktrace.a
-- Installing: /usr/local/lib/libabsl_flags_commandlineflag_internal.a
-- Installing: /usr/local/lib/libabsl_periodic_sampler.a
-- Installing: /usr/local/lib/libabsl_graphcycles_internal.a
-- Installing: /usr/local/lib/libabsl_crc_cpu_detect.a
-- Installing: /usr/local/lib/libabsl_flags_usage_internal.a
-- Installing: /usr/local/lib/libabsl_bad_optional_access.a
-- Installing: /usr/local/lib/libabsl_examine_stack.a
-- Installing: /usr/local/lib/libabsl_hash.a
-- Installing: /usr/local/lib/libClp.a
-- Installing: /usr/local/lib/libabsl_statusor.a
-- Installing: /usr/local/lib/libClpSolver.a
-- Installing: /usr/local/lib/libabsl_flags_private_handle_accessor.a
-- Installing: /usr/local/lib/libabsl_random_internal_platform.a
-- Up-to-date: /usr/local/share
-- Installing: /usr/local/share/doc
-- Installing: /usr/local/share/doc/ortools
-- Installing: /usr/local/share/doc/ortools/LICENSE
-- Up-to-date: /usr/local/share/man
-- Installing: /usr/local/share/man/man3
-- Installing: /usr/local/share/man/man3/zlib.3
-- Installing: /usr/local/share/pkgconfig
-- Installing: /usr/local/share/pkgconfig/zlib.pc
-- Installing: /usr/local/share/eigen3
-- Installing: /usr/local/share/eigen3/cmake
-- Installing: /usr/local/share/eigen3/cmake/Eigen3Targets.cmake
-- Installing: /usr/local/share/eigen3/cmake/Eigen3ConfigVersion.cmake
-- Installing: /usr/local/share/eigen3/cmake/Eigen3Config.cmake
-- Installing: /usr/local/share/eigen3/cmake/UseEigen3.cmake
-- Installing: /usr/local/share/minizinc
-- Installing: /usr/local/share/minizinc/solvers
-- Installing: /usr/local/share/minizinc/solvers/cpsat.msc
-- Installing: /usr/local/share/minizinc/cpsat
-- Installing: /usr/local/share/minizinc/cpsat/redefinitions-2.0.mzn
-- Installing: /usr/local/share/minizinc/cpsat/fzn_network_flow.mzn
-- Installing: /usr/local/share/minizinc/cpsat/nostrings.mzn
-- Installing: /usr/local/share/minizinc/cpsat/fzn_all_different_int.mzn
-- Installing: /usr/local/share/minizinc/cpsat/fzn_cumulative_opt.mzn
-- Installing: /usr/local/share/minizinc/cpsat/fzn_disjunctive_opt.mzn
-- Installing: /usr/local/share/minizinc/cpsat/fzn_subcircuit.mzn
-- Installing: /usr/local/share/minizinc/cpsat/fzn_disjunctive_strict.mzn
-- Installing: /usr/local/share/minizinc/cpsat/fzn_disjunctive.mzn
-- Installing: /usr/local/share/minizinc/cpsat/fzn_table_bool.mzn
-- Installing: /usr/local/share/minizinc/cpsat/fzn_circuit.mzn
-- Installing: /usr/local/share/minizinc/cpsat/fzn_diffn.mzn
-- Installing: /usr/local/share/minizinc/cpsat/fzn_regular.mzn
-- Installing: /usr/local/share/minizinc/cpsat/fzn_diffn_nonstrict.mzn
-- Installing: /usr/local/share/minizinc/cpsat/fzn_disjunctive_strict_opt.mzn
-- Installing: /usr/local/share/minizinc/cpsat/fzn_network_flow_cost.mzn
-- Installing: /usr/local/share/minizinc/cpsat/fzn_cumulative.mzn
-- Installing: /usr/local/share/minizinc/cpsat/fzn_table_int.mzn
-- Installing: /usr/local/share/minizinc/cpsat/fzn_inverse.mzn
-- Up-to-date: /usr/local/include
-- Installing: /usr/local/include/blockmemshell
-- Installing: /usr/local/include/blockmemshell/memory.h
-- Installing: /usr/local/include/xml
-- Installing: /usr/local/include/xml/xmldef.h
-- Installing: /usr/local/include/xml/xml.h
-- Installing: /usr/local/include/utf8_validity.h
-- Installing: /usr/local/include/scip
-- Installing: /usr/local/include/scip/cutsel.h
-- Installing: /usr/local/include/scip/expr_entropy.h
-- Installing: /usr/local/include/scip/pub_sepa.h
-- Installing: /usr/local/include/scip/heur_gins.h
-- Installing: /usr/local/include/scip/cons_cumulative.h
-- Installing: /usr/local/include/scip/heur_proximity.h
-- Installing: /usr/local/include/scip/scip_solvingstats.h
-- Installing: /usr/local/include/scip/reader_pip.h
-- Installing: /usr/local/include/scip/table_default.h
-- Installing: /usr/local/include/scip/struct_heur.h
-- Installing: /usr/local/include/scip/presol_domcol.h
-- Installing: /usr/local/include/scip/struct_misc.h
-- Installing: /usr/local/include/scip/bendersdefcuts.h
-- Installing: /usr/local/include/scip/heur_indicator.h
-- Installing: /usr/local/include/scip/prop_dualfix.h
-- Installing: /usr/local/include/scip/pricer.h
-- Installing: /usr/local/include/scip/prop.h
-- Installing: /usr/local/include/scip/sepa_oddcycle.h
-- Installing: /usr/local/include/scip/type_lp.h
-- Installing: /usr/local/include/scip/presol_qpkktref.h
-- Installing: /usr/local/include/scip/def.h
-- Installing: /usr/local/include/scip/struct_concsolver.h
-- Installing: /usr/local/include/scip/nlpi.h
-- Installing: /usr/local/include/scip/type_dialog.h
-- Installing: /usr/local/include/scip/struct_var.h
-- Installing: /usr/local/include/scip/nlpi_ipopt.h
-- Installing: /usr/local/include/scip/rbtree.h
-- Installing: /usr/local/include/scip/compr_largestrepr.h
-- Installing: /usr/local/include/scip/sepa_clique.h
-- Installing: /usr/local/include/scip/presol_sparsify.h
-- Installing: /usr/local/include/scip/event_softtimelimit.h
-- Installing: /usr/local/include/scip/cons_orbitope.h
-- Installing: /usr/local/include/scip/heur_twoopt.h
-- Installing: /usr/local/include/scip/struct_matrix.h
-- Installing: /usr/local/include/scip/branch_pscost.h
-- Installing: /usr/local/include/scip/type_pricer.h
-- Installing: /usr/local/include/scip/stat.h
-- Installing: /usr/local/include/scip/pub_cutsel.h
-- Installing: /usr/local/include/scip/reader_mps.h
-- Installing: /usr/local/include/scip/primal.h
-- Installing: /usr/local/include/scip/heur_completesol.h
-- Installing: /usr/local/include/scip/type_sepa.h
-- Installing: /usr/local/include/scip/heur_linesearchdiving.h
-- Installing: /usr/local/include/scip/type_cutpool.h
-- Installing: /usr/local/include/scip/branch_cloud.h
-- Installing: /usr/local/include/scip/heur_distributiondiving.h
-- Installing: /usr/local/include/scip/struct_nlhdlr.h
-- Installing: /usr/local/include/scip/cons_orbisack.h
-- Installing: /usr/local/include/scip/pub_message.h
-- Installing: /usr/local/include/scip/prop_pseudoobj.h
-- Installing: /usr/local/include/scip/pricestore.h
-- Installing: /usr/local/include/scip/branch_random.h
-- Installing: /usr/local/include/scip/scip_general.h
-- Installing: /usr/local/include/scip/heur_feaspump.h
-- Installing: /usr/local/include/scip/misc.h
-- Installing: /usr/local/include/scip/sepa_closecuts.h
-- Installing: /usr/local/include/scip/cons_bounddisjunction.h
-- Installing: /usr/local/include/scip/scipbuildflags.h
-- Installing: /usr/local/include/scip/dbldblarith.h
-- Installing: /usr/local/include/scip/mem.h
-- Installing: /usr/local/include/scip/exprinterpret.h
-- Installing: /usr/local/include/scip/type_tree.h
-- Installing: /usr/local/include/scip/scip_export.h
-- Installing: /usr/local/include/scip/type_stat.h
-- Installing: /usr/local/include/scip/compr_weakcompr.h
-- Installing: /usr/local/include/scip/heur_fixandinfer.h
-- Installing: /usr/local/include/scip/reader_rlp.h
-- Installing: /usr/local/include/scip/branch_vanillafullstrong.h
-- Installing: /usr/local/include/scip/scip_reopt.h
-- Installing: /usr/local/include/scip/sepa_impliedbounds.h
-- Installing: /usr/local/include/scip/nodesel_hybridestim.h
-- Installing: /usr/local/include/scip/cons_indicator.h
-- Installing: /usr/local/include/scip/expr_varidx.h
-- Installing: /usr/local/include/scip/reader_diff.h
-- Installing: /usr/local/include/scip/benderscut_int.h
-- Installing: /usr/local/include/scip/sepa.h
-- Installing: /usr/local/include/scip/cons_superindicator.h
-- Installing: /usr/local/include/scip/type_dcmp.h
-- Installing: /usr/local/include/scip/expr_value.h
-- Installing: /usr/local/include/scip/heur_oneopt.h
-- Installing: /usr/local/include/scip/cutpool.h
-- Installing: /usr/local/include/scip/reader_gms.h
-- Installing: /usr/local/include/scip/presol_implics.h
-- Installing: /usr/local/include/scip/type_set.h
-- Installing: /usr/local/include/scip/heur_lpface.h
-- Installing: /usr/local/include/scip/type_conflict.h
-- Installing: /usr/local/include/scip/config.h
-- Installing: /usr/local/include/scip/presolve.h
-- Installing: /usr/local/include/scip/heur_sync.h
-- Installing: /usr/local/include/scip/type_concsolver.h
-- Installing: /usr/local/include/scip/nodesel_uct.h
-- Installing: /usr/local/include/scip/bitencode.h
-- Installing: /usr/local/include/scip/presol_convertinttobin.h
-- Installing: /usr/local/include/scip/benders_default.h
-- Installing: /usr/local/include/scip/sepa_aggregation.h
-- Installing: /usr/local/include/scip/expr_sum.h
-- Installing: /usr/local/include/scip/struct_conflict.h
-- Installing: /usr/local/include/scip/scip_concurrent.h
-- Installing: /usr/local/include/scip/nlhdlr.h
-- Installing: /usr/local/include/scip/pub_misc_sort.h
-- Installing: /usr/local/include/scip/pub_fileio.h
-- Installing: /usr/local/include/scip/table.h
-- Installing: /usr/local/include/scip/type_expr.h
-- Installing: /usr/local/include/scip/pub_heur.h
-- Installing: /usr/local/include/scip/struct_reopt.h
-- Installing: /usr/local/include/scip/scip_conflict.h
-- Installing: /usr/local/include/scip/heur_mutation.h
-- Installing: /usr/local/include/scip/nlpioracle.h
-- Installing: /usr/local/include/scip/struct_message.h
-- Installing: /usr/local/include/scip/pub_lp.h
-- Installing: /usr/local/include/scip/type_scip.h
-- Installing: /usr/local/include/scip/scip_benders.h
-- Installing: /usr/local/include/scip/scip_nlpi.h
-- Installing: /usr/local/include/scip/interrupt.h
-- Installing: /usr/local/include/scip/scip_relax.h
-- Installing: /usr/local/include/scip/scip_sepa.h
-- Installing: /usr/local/include/scip/nlhdlr_quotient.h
-- Installing: /usr/local/include/scip/scip_dcmp.h
-- Installing: /usr/local/include/scip/nodesel_restartdfs.h
-- Installing: /usr/local/include/scip/syncstore.h
-- Installing: /usr/local/include/scip/branch_allfullstrong.h
-- Installing: /usr/local/include/scip/pub_implics.h
-- Installing: /usr/local/include/scip/pub_bandit_exp3.h
-- Installing: /usr/local/include/scip/heur_farkasdiving.h
-- Installing: /usr/local/include/scip/heur_conflictdiving.h
-- Installing: /usr/local/include/scip/struct_set.h
-- Installing: /usr/local/include/scip/sol.h
-- Installing: /usr/local/include/scip/prop_probing.h
-- Installing: /usr/local/include/scip/scip_cutsel.h
-- Installing: /usr/local/include/scip/type_visual.h
-- Installing: /usr/local/include/scip/heur_rounding.h
-- Installing: /usr/local/include/scip/cons_disjunction.h
-- Installing: /usr/local/include/scip/history.h
-- Installing: /usr/local/include/scip/pub_nlhdlr.h
-- Installing: /usr/local/include/scip/nlpi_filtersqp.h
-- Installing: /usr/local/include/scip/reader_cnf.h
-- Installing: /usr/local/include/scip/pub_cutpool.h
-- Installing: /usr/local/include/scip/scip_validation.h
-- Installing: /usr/local/include/scip/presol.h
-- Installing: /usr/local/include/scip/cons_countsols.h
-- Installing: /usr/local/include/scip/cons_and.h
-- Installing: /usr/local/include/scip/branch_leastinf.h
-- Installing: /usr/local/include/scip/lp.h
-- Installing: /usr/local/include/scip/dcmp.h
-- Installing: /usr/local/include/scip/cons.h
-- Installing: /usr/local/include/scip/pub_misc_rowprep.h
-- Installing: /usr/local/include/scip/treemodel.h
-- Installing: /usr/local/include/scip/scip_sol.h
-- Installing: /usr/local/include/scip/pub_reader.h
-- Installing: /usr/local/include/scip/bandit_epsgreedy.h
-- Installing: /usr/local/include/scip/benderscut_nogood.h
-- Installing: /usr/local/include/scip/prop_nlobbt.h
-- Installing: /usr/local/include/scip/heur_shifting.h
-- Installing: /usr/local/include/scip/struct_scip.h
-- Installing: /usr/local/include/scip/type_heur.h
-- Installing: /usr/local/include/scip/set.h
-- Installing: /usr/local/include/scip/prop_rootredcost.h
-- Installing: /usr/local/include/scip/type_nlp.h
-- Installing: /usr/local/include/scip/type_retcode.h
-- Installing: /usr/local/include/scip/heur_fracdiving.h
-- Installing: /usr/local/include/scip/branch_inference.h
-- Installing: /usr/local/include/scip/cons_components.h
-- Installing: /usr/local/include/scip/scip_heur.h
-- Installing: /usr/local/include/scip/expr_trig.h
-- Installing: /usr/local/include/scip/cons_integral.h
-- Installing: /usr/local/include/scip/pub_bandit.h
-- Installing: /usr/local/include/scip/scip_debug.h
-- Installing: /usr/local/include/scip/heur_trivial.h
-- Installing: /usr/local/include/scip/nlhdlr_perspective.h
-- Installing: /usr/local/include/scip/type_nodesel.h
-- Installing: /usr/local/include/scip/solve.h
-- Installing: /usr/local/include/scip/message.h
-- Installing: /usr/local/include/scip/scip_copy.h
-- Installing: /usr/local/include/scip/scip_tree.h
-- Installing: /usr/local/include/scip/reader_fzn.h
-- Installing: /usr/local/include/scip/scip_event.h
-- Installing: /usr/local/include/scip/reader_bnd.h
-- Installing: /usr/local/include/scip/struct_expr.h
-- Installing: /usr/local/include/scip/type_conflictstore.h
-- Installing: /usr/local/include/scip/struct_syncstore.h
-- Installing: /usr/local/include/scip/heur_octane.h
-- Installing: /usr/local/include/scip/expr.h
-- Installing: /usr/local/include/scip/type_timing.h
-- Installing: /usr/local/include/scip/heur_reoptsols.h
-- Installing: /usr/local/include/scip/dialog_default.h
-- Installing: /usr/local/include/scip/struct_dialog.h
-- Installing: /usr/local/include/scip/heur_shiftandpropagate.h
-- Installing: /usr/local/include/scip/struct_history.h
-- Installing: /usr/local/include/scip/cons_abspower.h
-- Installing: /usr/local/include/scip/disp_default.h
-- Installing: /usr/local/include/scip/clock.h
-- Installing: /usr/local/include/scip/compr.h
-- Installing: /usr/local/include/scip/scip_param.h
-- Installing: /usr/local/include/scip/cons_sos1.h
-- Installing: /usr/local/include/scip/pub_branch.h
-- Installing: /usr/local/include/scip/presol_boundshift.h
-- Installing: /usr/local/include/scip/presol_dualagg.h
-- Installing: /usr/local/include/scip/scip_cut.h
-- Installing: /usr/local/include/scip/struct_lp.h
-- Installing: /usr/local/include/scip/type_history.h
-- Installing: /usr/local/include/scip/presol_stuffing.h
-- Installing: /usr/local/include/scip/conflictstore.h
-- Installing: /usr/local/include/scip/scip_dialog.h
-- Installing: /usr/local/include/scip/type_benders.h
-- Installing: /usr/local/include/scip/benderscut_opt.h
-- Installing: /usr/local/include/scip/cuts.h
-- Installing: /usr/local/include/scip/type_nlhdlr.h
-- Installing: /usr/local/include/scip/nodesel.h
-- Installing: /usr/local/include/scip/bandit.h
-- Installing: /usr/local/include/scip/cons_soc.h
-- Installing: /usr/local/include/scip/pub_nlp.h
-- Installing: /usr/local/include/scip/type_sol.h
-- Installing: /usr/local/include/scip/pub_disp.h
-- Installing: /usr/local/include/scip/pub_misc.h
-- Installing: /usr/local/include/scip/pub_misc_linear.h
-- Installing: /usr/local/include/scip/prop_genvbounds.h
-- Installing: /usr/local/include/scip/scip_message.h
-- Installing: /usr/local/include/scip/benderscut_feas.h
-- Installing: /usr/local/include/scip/heur.h
-- Installing: /usr/local/include/scip/event_globalbnd.h
-- Installing: /usr/local/include/scip/type_branch.h
-- Installing: /usr/local/include/scip/scip_var.h
-- Installing: /usr/local/include/scip/reader_sol.h
-- Installing: /usr/local/include/scip/heur_trysol.h
-- Installing: /usr/local/include/scip/type_mem.h
-- Installing: /usr/local/include/scip/cons_varbound.h
-- Installing: /usr/local/include/scip/scip_prob.h
-- Installing: /usr/local/include/scip/presol_inttobinary.h
-- Installing: /usr/local/include/scip/reader_osil.h
-- Installing: /usr/local/include/scip/struct_sepastore.h
-- Installing: /usr/local/include/scip/struct_tree.h
-- Installing: /usr/local/include/scip/cons_logicor.h
-- Installing: /usr/local/include/scip/scip_numerics.h
-- Installing: /usr/local/include/scip/type_bandit.h
-- Installing: /usr/local/include/scip/struct_prop.h
-- Installing: /usr/local/include/scip/type_exprinterpret.h
-- Installing: /usr/local/include/scip/sepa_convexproj.h
-- Installing: /usr/local/include/scip/var.h
-- Installing: /usr/local/include/scip/presol_tworowbnd.h
-- Installing: /usr/local/include/scip/heur_zirounding.h
-- Installing: /usr/local/include/scip/nlhdlr_soc.h
-- Installing: /usr/local/include/scip/type_prop.h
-- Installing: /usr/local/include/scip/retcode.h
-- Installing: /usr/local/include/scip/heur_ofins.h
-- Installing: /usr/local/include/scip/intervalarith.h
-- Installing: /usr/local/include/scip/struct_cuts.h
-- Installing: /usr/local/include/scip/type_benderscut.h
-- Installing: /usr/local/include/scip/tree.h
-- Installing: /usr/local/include/scip/pub_dcmp.h
-- Installing: /usr/local/include/scip/expr_exp.h
-- Installing: /usr/local/include/scip/cons_knapsack.h
-- Installing: /usr/local/include/scip/presol_redvub.h
-- Installing: /usr/local/include/scip/type_clock.h
-- Installing: /usr/local/include/scip/scip_presol.h
-- Installing: /usr/local/include/scip/struct_stat.h
-- Installing: /usr/local/include/scip/sepa_mcf.h
-- Installing: /usr/local/include/scip/presol_dualinfer.h
-- Installing: /usr/local/include/scip/heur_objpscostdiving.h
-- Installing: /usr/local/include/scip/cons_cardinality.h
-- Installing: /usr/local/include/scip/sepastore.h
-- Installing: /usr/local/include/scip/sepa_minor.h
-- Installing: /usr/local/include/scip/struct_sepa.h
-- Installing: /usr/local/include/scip/type_disp.h
-- Installing: /usr/local/include/scip/expr_var.h
-- Installing: /usr/local/include/scip/nodesel_breadthfirst.h
-- Installing: /usr/local/include/scip/heur_rins.h
-- Installing: /usr/local/include/scip/branch_multaggr.h
-- Installing: /usr/local/include/scip/type_cuts.h
-- Installing: /usr/local/include/scip/type_result.h
-- Installing: /usr/local/include/scip/cons_or.h
-- Installing: /usr/local/include/scip/scip_pricer.h
-- Installing: /usr/local/include/scip/scipcoreplugins.h
-- Installing: /usr/local/include/scip/scipdefplugins.h
-- Installing: /usr/local/include/scip/paramset.h
-- Installing: /usr/local/include/scip/pub_dialog.h
-- Installing: /usr/local/include/scip/heur_pscostdiving.h
-- Installing: /usr/local/include/scip/benders.h
-- Installing: /usr/local/include/scip/pub_presol.h
-- Installing: /usr/local/include/scip/pub_nodesel.h
-- Installing: /usr/local/include/scip/benderscut.h
-- Installing: /usr/local/include/scip/heur_dps.h
-- Installing: /usr/local/include/scip/branch.h
-- Installing: /usr/local/include/scip/event_solvingphase.h
-- Installing: /usr/local/include/scip/type_matrix.h
-- Installing: /usr/local/include/scip/pub_tree.h
-- Installing: /usr/local/include/scip/cons_linear.h
-- Installing: /usr/local/include/scip/scip_nlp.h
-- Installing: /usr/local/include/scip/struct_cutsel.h
-- Installing: /usr/local/include/scip/struct_nodesel.h
-- Installing: /usr/local/include/scip/disp.h
-- Installing: /usr/local/include/scip/scipshell.h
-- Installing: /usr/local/include/scip/reader_fix.h
-- Installing: /usr/local/include/scip/sepa_cgmip.h
-- Installing: /usr/local/include/scip/scip_randnumgen.h
-- Installing: /usr/local/include/scip/dialog.h
-- Installing: /usr/local/include/scip/pub_expr.h
-- Installing: /usr/local/include/scip/scip_cons.h
-- Installing: /usr/local/include/scip/pub_sol.h
-- Installing: /usr/local/include/scip/heur_alns.h
-- Installing: /usr/local/include/scip/scip_probing.h
-- Installing: /usr/local/include/scip/scip_table.h
-- Installing: /usr/local/include/scip/pub_prop.h
-- Installing: /usr/local/include/scip/bandit_exp3.h
-- Installing: /usr/local/include/scip/struct_bandit.h
-- Installing: /usr/local/include/scip/struct_implics.h
-- Installing: /usr/local/include/scip/type_presol.h
-- Installing: /usr/local/include/scip/type_reader.h
-- Installing: /usr/local/include/scip/struct_relax.h
-- Installing: /usr/local/include/scip/type_sepastore.h
-- Installing: /usr/local/include/scip/sepa_zerohalf.h
-- Installing: /usr/local/include/scip/type_nlpi.h
-- Installing: /usr/local/include/scip/benderscut_feasalt.h
-- Installing: /usr/local/include/scip/concsolver_scip.h
-- Installing: /usr/local/include/scip/struct_nlp.h
-- Installing: /usr/local/include/scip/boundstore.h
-- Installing: /usr/local/include/scip/type_var.h
-- Installing: /usr/local/include/scip/heur_nlpdiving.h
-- Installing: /usr/local/include/scip/expr_erf.h
-- Installing: /usr/local/include/scip/heur_rootsoldiving.h
-- Installing: /usr/local/include/scip/pub_nlpi.h
-- Installing: /usr/local/include/scip/heur_guideddiving.h
-- Installing: /usr/local/include/scip/struct_clock.h
-- Installing: /usr/local/include/scip/prop_obbt.h
-- Installing: /usr/local/include/scip/pub_paramset.h
-- Installing: /usr/local/include/scip/reader_zpl.h
-- Installing: /usr/local/include/scip/pub_benderscut.h
-- Installing: /usr/local/include/scip/heur_coefdiving.h
-- Installing: /usr/local/include/scip/branch_mostinf.h
-- Installing: /usr/local/include/scip/nlp.h
-- Installing: /usr/local/include/scip/reader_lp.h
-- Installing: /usr/local/include/scip/prop_redcost.h
-- Installing: /usr/local/include/scip/heur_zeroobj.h
-- Installing: /usr/local/include/scip/nlhdlr_default.h
-- Installing: /usr/local/include/scip/bandit_ucb.h
-- Installing: /usr/local/include/scip/cons_symresack.h
-- Installing: /usr/local/include/scip/struct_cutpool.h
-- Installing: /usr/local/include/scip/pub_bandit_epsgreedy.h
-- Installing: /usr/local/include/scip/heur_padm.h
-- Installing: /usr/local/include/scip/type_pricestore.h
-- Installing: /usr/local/include/scip/scip_compr.h
-- Installing: /usr/local/include/scip/reader_ccg.h
-- Installing: /usr/local/include/scip/struct_branch.h
-- Installing: /usr/local/include/scip/presol_dualsparsify.h
-- Installing: /usr/local/include/scip/pub_conflict.h
-- Installing: /usr/local/include/scip/scip_branch.h
-- Installing: /usr/local/include/scip/nlhdlr_bilinear.h
-- Installing: /usr/local/include/scip/struct_disp.h
-- Installing: /usr/local/include/scip/implics.h
-- Installing: /usr/local/include/scip/heur_locks.h
-- Installing: /usr/local/include/scip/reader_wbo.h
-- Installing: /usr/local/include/scip/presol_milp.h
-- Installing: /usr/local/include/scip/sepa_rlt.h
-- Installing: /usr/local/include/scip/struct_prob.h
-- Installing: /usr/local/include/scip/scip_mem.h
-- Installing: /usr/local/include/scip/pub_reopt.h
-- Installing: /usr/local/include/scip/sepa_disjunctive.h
-- Installing: /usr/local/include/scip/debug.h
-- Installing: /usr/local/include/scip/scip_solve.h
-- Installing: /usr/local/include/scip/reader_cip.h
-- Installing: /usr/local/include/scip/cons_sos2.h
-- Installing: /usr/local/include/scip/prop_sync.h
-- Installing: /usr/local/include/scip/type_prob.h
-- Installing: /usr/local/include/scip/prop_vbounds.h
-- Installing: /usr/local/include/scip/type_interrupt.h
-- Installing: /usr/local/include/scip/cons_benders.h
-- Installing: /usr/local/include/scip/cons_nonlinear.h
-- Installing: /usr/local/include/scip/scip_reader.h
-- Installing: /usr/local/include/scip/cons_quadratic.h
-- Installing: /usr/local/include/scip/pub_misc_select.h
-- Installing: /usr/local/include/scip/pub_cons.h
-- Installing: /usr/local/include/scip/cons_conjunction.h
-- Installing: /usr/local/include/scip/pub_var.h
-- Installing: /usr/local/include/scip/struct_sol.h
-- Installing: /usr/local/include/scip/sepa_eccuts.h
-- Installing: /usr/local/include/scip/sepa_interminor.h
-- Installing: /usr/local/include/scip/message_default.h
-- Installing: /usr/local/include/scip/reopt.h
-- Installing: /usr/local/include/scip/prop_symmetry.h
-- Installing: /usr/local/include/scip/scip_timing.h
-- Installing: /usr/local/include/scip/cons_setppc.h
-- Installing: /usr/local/include/scip/nodesel_dfs.h
-- Installing: /usr/local/include/scip/pub_bandit_ucb.h
-- Installing: /usr/local/include/scip/heur_randrounding.h
-- Installing: /usr/local/include/scip/scip.h
-- Installing: /usr/local/include/scip/reader_dec.h
-- Installing: /usr/local/include/scip/struct_presol.h
-- Installing: /usr/local/include/scip/heur_repair.h
-- Installing: /usr/local/include/scip/scip_expr.h
-- Installing: /usr/local/include/scip/pub_matrix.h
-- Installing: /usr/local/include/scip/sepa_intobj.h
-- Installing: /usr/local/include/scip/expr_pow.h
-- Installing: /usr/local/include/scip/pub_pricer.h
-- Installing: /usr/local/include/scip/pub_compr.h
-- Installing: /usr/local/include/scip/struct_mem.h
-- Installing: /usr/local/include/scip/nlhdlr_convex.h
-- Installing: /usr/local/include/scip/heur_trustregion.h
-- Installing: /usr/local/include/scip/struct_cons.h
-- Installing: /usr/local/include/scip/reader_sto.h
-- Installing: /usr/local/include/scip/scip_bandit.h
-- Installing: /usr/local/include/scip/cons_xor.h
-- Installing: /usr/local/include/scip/heur_undercover.h
-- Installing: /usr/local/include/scip/struct_dcmp.h
-- Installing: /usr/local/include/scip/struct_reader.h
-- Installing: /usr/local/include/scip/type_paramset.h
-- Installing: /usr/local/include/scip/expr_abs.h
-- Installing: /usr/local/include/scip/reader_pbm.h
-- Installing: /usr/local/include/scip/heuristics.h
-- Installing: /usr/local/include/scip/presol_gateextraction.h
-- Installing: /usr/local/include/scip/expr_log.h
-- Installing: /usr/local/include/scip/heur_dins.h
-- Installing: /usr/local/include/scip/reader_opb.h
-- Installing: /usr/local/include/scip/heur_simplerounding.h
-- Installing: /usr/local/include/scip/struct_nlpi.h
-- Installing: /usr/local/include/scip/reader_mst.h
-- Installing: /usr/local/include/scip/presol_trivial.h
-- Installing: /usr/local/include/scip/prob.h
-- Installing: /usr/local/include/scip/heur_bound.h
-- Installing: /usr/local/include/scip/nodesel_estimate.h
-- Installing: /usr/local/include/scip/heur_intdiving.h
-- Installing: /usr/local/include/scip/heur_vbounds.h
-- Installing: /usr/local/include/scip/cons_pseudoboolean.h
-- Installing: /usr/local/include/scip/pub_event.h
-- Installing: /usr/local/include/scip/pub_history.h
-- Installing: /usr/local/include/scip/heur_multistart.h
-- Installing: /usr/local/include/scip/scip_datastructures.h
-- Installing: /usr/local/include/scip/sepa_mixing.h
-- Installing: /usr/local/include/scip/scip_prop.h
-- Installing: /usr/local/include/scip/type_syncstore.h
-- Installing: /usr/local/include/scip/heur_rens.h
-- Installing: /usr/local/include/scip/pub_relax.h
-- Installing: /usr/local/include/scip/scip_disp.h
-- Installing: /usr/local/include/scip/symmetry.h
-- Installing: /usr/local/include/scip/heur_adaptivediving.h
-- Installing: /usr/local/include/scip/nlpi_worhp.h
-- Installing: /usr/local/include/scip/struct_event.h
-- Installing: /usr/local/include/scip/type_compr.h
-- Installing: /usr/local/include/scip/type_misc.h
-- Installing: /usr/local/include/scip/cons_linking.h
-- Installing: /usr/local/include/scip/scip_lp.h
-- Installing: /usr/local/include/scip/scip_nodesel.h
-- Installing: /usr/local/include/scip/heur_clique.h
-- Installing: /usr/local/include/scip/type_cons.h
-- Installing: /usr/local/include/scip/concurrent.h
-- Installing: /usr/local/include/scip/struct_benders.h
-- Installing: /usr/local/include/scip/scipgithash.h
-- Installing: /usr/local/include/scip/heur_subnlp.h
-- Installing: /usr/local/include/scip/struct_table.h
-- Installing: /usr/local/include/scip/type_implics.h
-- Installing: /usr/local/include/scip/type_cutsel.h
-- Installing: /usr/local/include/scip/heur_veclendiving.h
-- Installing: /usr/local/include/scip/type_event.h
-- Installing: /usr/local/include/scip/type_concurrent.h
-- Installing: /usr/local/include/scip/heur_trivialnegation.h
-- Installing: /usr/local/include/scip/sepa_gauge.h
-- Installing: /usr/local/include/scip/struct_pricestore.h
-- Installing: /usr/local/include/scip/reader_ppm.h
-- Installing: /usr/local/include/scip/branch_distribution.h
-- Installing: /usr/local/include/scip/relax.h
-- Installing: /usr/local/include/scip/struct_compr.h
-- Installing: /usr/local/include/scip/expr_product.h
-- Installing: /usr/local/include/scip/reader_smps.h
-- Installing: /usr/local/include/scip/struct_visual.h
-- Installing: /usr/local/include/scip/branch_relpscost.h
-- Installing: /usr/local/include/scip/cutsel_hybrid.h
-- Installing: /usr/local/include/scip/cons_benderslp.h
-- Installing: /usr/local/include/scip/event_estim.h
-- Installing: /usr/local/include/scip/type_reopt.h
-- Installing: /usr/local/include/scip/pub_benders.h
-- Installing: /usr/local/include/scip/struct_conflictstore.h
-- Installing: /usr/local/include/scip/reader_nl.h
-- Installing: /usr/local/include/scip/reader_tim.h
-- Installing: /usr/local/include/scip/type_relax.h
-- Installing: /usr/local/include/scip/presol_dualcomp.h
-- Installing: /usr/local/include/scip/type_message.h
-- Installing: /usr/local/include/scip/heur_dualval.h
-- Installing: /usr/local/include/scip/branch_lookahead.h
-- Installing: /usr/local/include/scip/struct_pricer.h
-- Installing: /usr/local/include/scip/reader_cor.h
-- Installing: /usr/local/include/scip/visual.h
-- Installing: /usr/local/include/scip/struct_concurrent.h
-- Installing: /usr/local/include/scip/branch_nodereopt.h
-- Installing: /usr/local/include/scip/nlhdlr_quadratic.h
-- Installing: /usr/local/include/scip/nlpi_all.h
-- Installing: /usr/local/include/scip/nodesel_bfs.h
-- Installing: /usr/local/include/scip/struct_benderscut.h
-- Installing: /usr/local/include/scip/heur_mpec.h
-- Installing: /usr/local/include/scip/concsolver.h
-- Installing: /usr/local/include/scip/reader.h
-- Installing: /usr/local/include/scip/heur_localbranching.h
-- Installing: /usr/local/include/scip/struct_primal.h
-- Installing: /usr/local/include/scip/event.h
-- Installing: /usr/local/include/scip/heur_intshifting.h
-- Installing: /usr/local/include/scip/heur_actconsdiving.h
-- Installing: /usr/local/include/scip/branch_fullstrong.h
-- Installing: /usr/local/include/scip/type_table.h
-- Installing: /usr/local/include/scip/heur_crossover.h
-- Installing: /usr/local/include/scip/type_primal.h
-- Installing: /usr/local/include/scip/sepa_gomory.h
-- Installing: /usr/local/include/scip/pub_table.h
-- Installing: /usr/local/include/scip/struct_paramset.h
-- Installing: /usr/local/include/scip/sepa_rapidlearning.h
-- Installing: /usr/local/include/scip/conflict.h
-- Installing: /usr/local/include/symmetry
-- Installing: /usr/local/include/symmetry/type_symmetry.h
-- Installing: /usr/local/include/symmetry/compute_symmetry.h
-- Installing: /usr/local/include/dijkstra
-- Installing: /usr/local/include/dijkstra/dijkstra.h
-- Installing: /usr/local/include/zlib.h
-- Installing: /usr/local/include/tclique
-- Installing: /usr/local/include/tclique/tclique.h
-- Installing: /usr/local/include/tclique/tclique_def.h
-- Installing: /usr/local/include/tclique/tclique_coloring.h
-- Installing: /usr/local/include/zconf.h
-- Installing: /usr/local/include/tinycthread
-- Installing: /usr/local/include/tinycthread/tinycthread.h
-- Installing: /usr/local/include/objscip
-- Installing: /usr/local/include/objscip/objcloneable.h
-- Installing: /usr/local/include/objscip/objcutsel.h
-- Installing: /usr/local/include/objscip/objprobcloneable.h
-- Installing: /usr/local/include/objscip/objpricer.h
-- Installing: /usr/local/include/objscip/objdialog.h
-- Installing: /usr/local/include/objscip/objnodesel.h
-- Installing: /usr/local/include/objscip/objbenderscut.h
-- Installing: /usr/local/include/objscip/objbranchrule.h
-- Installing: /usr/local/include/objscip/objconshdlr.h
-- Installing: /usr/local/include/objscip/objmessagehdlr.h
-- Installing: /usr/local/include/objscip/objbenders.h
-- Installing: /usr/local/include/objscip/type_objcloneable.h
-- Installing: /usr/local/include/objscip/objrelax.h
-- Installing: /usr/local/include/objscip/objdisp.h
-- Installing: /usr/local/include/objscip/objscipdefplugins.h
-- Installing: /usr/local/include/objscip/objtable.h
-- Installing: /usr/local/include/objscip/objsepa.h
-- Installing: /usr/local/include/objscip/objeventhdlr.h
-- Installing: /usr/local/include/objscip/objreader.h
-- Installing: /usr/local/include/objscip/objheur.h
-- Installing: /usr/local/include/objscip/objvardata.h
-- Installing: /usr/local/include/objscip/objpresol.h
-- Installing: /usr/local/include/objscip/type_objprobcloneable.h
-- Installing: /usr/local/include/objscip/objprop.h
-- Installing: /usr/local/include/objscip/objprobdata.h
-- Installing: /usr/local/include/objscip/objscip.h
-- Installing: /usr/local/include/absl
-- Installing: /usr/local/include/absl/functional
-- Installing: /usr/local/include/absl/functional/function_ref.h
-- Installing: /usr/local/include/absl/functional/overload.h
-- Installing: /usr/local/include/absl/functional/internal
-- Installing: /usr/local/include/absl/functional/internal/front_binder.h
-- Installing: /usr/local/include/absl/functional/internal/function_ref.h
-- Installing: /usr/local/include/absl/functional/internal/any_invocable.h
-- Installing: /usr/local/include/absl/functional/bind_front.h
-- Installing: /usr/local/include/absl/functional/any_invocable.h
-- Installing: /usr/local/include/absl/debugging
-- Installing: /usr/local/include/absl/debugging/symbolize_elf.inc
-- Installing: /usr/local/include/absl/debugging/symbolize_darwin.inc
-- Installing: /usr/local/include/absl/debugging/symbolize_win32.inc
-- Installing: /usr/local/include/absl/debugging/symbolize_emscripten.inc
-- Installing: /usr/local/include/absl/debugging/failure_signal_handler.h
-- Installing: /usr/local/include/absl/debugging/leak_check.h
-- Installing: /usr/local/include/absl/debugging/internal
-- Installing: /usr/local/include/absl/debugging/internal/stacktrace_arm-inl.inc
-- Installing: /usr/local/include/absl/debugging/internal/stacktrace_win32-inl.inc
-- Installing: /usr/local/include/absl/debugging/internal/vdso_support.h
-- Installing: /usr/local/include/absl/debugging/internal/examine_stack.h
-- Installing: /usr/local/include/absl/debugging/internal/stacktrace_powerpc-inl.inc
-- Installing: /usr/local/include/absl/debugging/internal/stacktrace_riscv-inl.inc
-- Installing: /usr/local/include/absl/debugging/internal/stacktrace_generic-inl.inc
-- Installing: /usr/local/include/absl/debugging/internal/stack_consumption.h
-- Installing: /usr/local/include/absl/debugging/internal/stacktrace_aarch64-inl.inc
-- Installing: /usr/local/include/absl/debugging/internal/stacktrace_x86-inl.inc
-- Installing: /usr/local/include/absl/debugging/internal/address_is_readable.h
-- Installing: /usr/local/include/absl/debugging/internal/demangle.h
-- Installing: /usr/local/include/absl/debugging/internal/stacktrace_unimplemented-inl.inc
-- Installing: /usr/local/include/absl/debugging/internal/symbolize.h
-- Installing: /usr/local/include/absl/debugging/internal/stacktrace_emscripten-inl.inc
-- Installing: /usr/local/include/absl/debugging/internal/stacktrace_config.h
-- Installing: /usr/local/include/absl/debugging/internal/elf_mem_image.h
-- Installing: /usr/local/include/absl/debugging/stacktrace.h
-- Installing: /usr/local/include/absl/debugging/symbolize.h
-- Installing: /usr/local/include/absl/debugging/symbolize_unimplemented.inc
-- Installing: /usr/local/include/absl/algorithm
-- Installing: /usr/local/include/absl/algorithm/algorithm.h
-- Installing: /usr/local/include/absl/algorithm/container.h
-- Installing: /usr/local/include/absl/time
-- Installing: /usr/local/include/absl/time/clock.h
-- Installing: /usr/local/include/absl/time/time.h
-- Installing: /usr/local/include/absl/time/internal
-- Installing: /usr/local/include/absl/time/internal/test_util.h
-- Installing: /usr/local/include/absl/time/internal/get_current_time_chrono.inc
-- Installing: /usr/local/include/absl/time/internal/cctz
-- Installing: /usr/local/include/absl/time/internal/cctz/include
-- Installing: /usr/local/include/absl/time/internal/cctz/include/cctz
-- Installing: /usr/local/include/absl/time/internal/cctz/include/cctz/zone_info_source.h
-- Installing: /usr/local/include/absl/time/internal/cctz/include/cctz/civil_time_detail.h
-- Installing: /usr/local/include/absl/time/internal/cctz/include/cctz/time_zone.h
-- Installing: /usr/local/include/absl/time/internal/cctz/include/cctz/civil_time.h
-- Installing: /usr/local/include/absl/time/internal/cctz/src
-- Installing: /usr/local/include/absl/time/internal/cctz/src/time_zone_info.h
-- Installing: /usr/local/include/absl/time/internal/cctz/src/time_zone_fixed.h
-- Installing: /usr/local/include/absl/time/internal/cctz/src/tzfile.h
-- Installing: /usr/local/include/absl/time/internal/cctz/src/time_zone_posix.h
-- Installing: /usr/local/include/absl/time/internal/cctz/src/time_zone_if.h
-- Installing: /usr/local/include/absl/time/internal/cctz/src/time_zone_libc.h
-- Installing: /usr/local/include/absl/time/internal/cctz/src/time_zone_impl.h
-- Installing: /usr/local/include/absl/time/internal/get_current_time_posix.inc
-- Installing: /usr/local/include/absl/time/civil_time.h
-- Installing: /usr/local/include/absl/crc
-- Installing: /usr/local/include/absl/crc/internal
-- Installing: /usr/local/include/absl/crc/internal/crc32_x86_arm_combined_simd.h
-- Installing: /usr/local/include/absl/crc/internal/crc.h
-- Installing: /usr/local/include/absl/crc/internal/cpu_detect.h
-- Installing: /usr/local/include/absl/crc/internal/non_temporal_arm_intrinsics.h
-- Installing: /usr/local/include/absl/crc/internal/crc32c.h
-- Installing: /usr/local/include/absl/crc/internal/crc32c_inline.h
-- Installing: /usr/local/include/absl/crc/internal/crc_memcpy.h
-- Installing: /usr/local/include/absl/crc/internal/crc_cord_state.h
-- Installing: /usr/local/include/absl/crc/internal/non_temporal_memcpy.h
-- Installing: /usr/local/include/absl/crc/internal/crc_internal.h
-- Installing: /usr/local/include/absl/crc/crc32c.h
-- Installing: /usr/local/include/absl/memory
-- Installing: /usr/local/include/absl/memory/memory.h
-- Installing: /usr/local/include/absl/strings
-- Installing: /usr/local/include/absl/strings/cord_buffer.h
-- Installing: /usr/local/include/absl/strings/str_format.h
-- Installing: /usr/local/include/absl/strings/has_ostream_operator.h
-- Installing: /usr/local/include/absl/strings/str_split.h
-- Installing: /usr/local/include/absl/strings/escaping.h
-- Installing: /usr/local/include/absl/strings/numbers.h
-- Installing: /usr/local/include/absl/strings/str_replace.h
-- Installing: /usr/local/include/absl/strings/substitute.h
-- Installing: /usr/local/include/absl/strings/charconv.h
-- Installing: /usr/local/include/absl/strings/internal
-- Installing: /usr/local/include/absl/strings/internal/cord_rep_consume.h
-- Installing: /usr/local/include/absl/strings/internal/stl_type_traits.h
-- Installing: /usr/local/include/absl/strings/internal/string_constant.h
-- Installing: /usr/local/include/absl/strings/internal/cord_rep_flat.h
-- Installing: /usr/local/include/absl/strings/internal/cordz_sample_token.h
-- Installing: /usr/local/include/absl/strings/internal/cord_internal.h
-- Installing: /usr/local/include/absl/strings/internal/stringify_sink.h
-- Installing: /usr/local/include/absl/strings/internal/cord_data_edge.h
-- Installing: /usr/local/include/absl/strings/internal/pow10_helper.h
-- Installing: /usr/local/include/absl/strings/internal/escaping.h
-- Installing: /usr/local/include/absl/strings/internal/ostringstream.h
-- Installing: /usr/local/include/absl/strings/internal/escaping_test_common.h
-- Installing: /usr/local/include/absl/strings/internal/charconv_parse.h
-- Installing: /usr/local/include/absl/strings/internal/cord_rep_btree.h
-- Installing: /usr/local/include/absl/strings/internal/str_format
-- Installing: /usr/local/include/absl/strings/internal/str_format/arg.h
-- Installing: /usr/local/include/absl/strings/internal/str_format/parser.h
-- Installing: /usr/local/include/absl/strings/internal/str_format/output.h
-- Installing: /usr/local/include/absl/strings/internal/str_format/checker.h
-- Installing: /usr/local/include/absl/strings/internal/str_format/bind.h
-- Installing: /usr/local/include/absl/strings/internal/str_format/extension.h
-- Installing: /usr/local/include/absl/strings/internal/str_format/float_conversion.h
-- Installing: /usr/local/include/absl/strings/internal/str_format/constexpr_parser.h
-- Installing: /usr/local/include/absl/strings/internal/cord_rep_btree_reader.h
-- Installing: /usr/local/include/absl/strings/internal/cordz_statistics.h
-- Installing: /usr/local/include/absl/strings/internal/cordz_handle.h
-- Installing: /usr/local/include/absl/strings/internal/cord_rep_btree_navigator.h
-- Installing: /usr/local/include/absl/strings/internal/cordz_functions.h
-- Installing: /usr/local/include/absl/strings/internal/resize_uninitialized.h
-- Installing: /usr/local/include/absl/strings/internal/utf8.h
-- Installing: /usr/local/include/absl/strings/internal/cord_rep_crc.h
-- Installing: /usr/local/include/absl/strings/internal/cord_rep_test_util.h
-- Installing: /usr/local/include/absl/strings/internal/cordz_update_tracker.h
-- Installing: /usr/local/include/absl/strings/internal/cordz_info.h
-- Installing: /usr/local/include/absl/strings/internal/str_split_internal.h
-- Installing: /usr/local/include/absl/strings/internal/charconv_bigint.h
-- Installing: /usr/local/include/absl/strings/internal/str_join_internal.h
-- Installing: /usr/local/include/absl/strings/internal/numbers_test_common.h
-- Installing: /usr/local/include/absl/strings/internal/cordz_update_scope.h
-- Installing: /usr/local/include/absl/strings/internal/damerau_levenshtein_distance.h
-- Installing: /usr/local/include/absl/strings/internal/has_absl_stringify.h
-- Installing: /usr/local/include/absl/strings/internal/memutil.h
-- Installing: /usr/local/include/absl/strings/cord_test_helpers.h
-- Installing: /usr/local/include/absl/strings/match.h
-- Installing: /usr/local/include/absl/strings/str_cat.h
-- Installing: /usr/local/include/absl/strings/strip.h
-- Installing: /usr/local/include/absl/strings/ascii.h
-- Installing: /usr/local/include/absl/strings/cord.h
-- Installing: /usr/local/include/absl/strings/str_join.h
-- Installing: /usr/local/include/absl/strings/cord_analysis.h
-- Installing: /usr/local/include/absl/strings/has_absl_stringify.h
-- Installing: /usr/local/include/absl/strings/cordz_test_helpers.h
-- Installing: /usr/local/include/absl/strings/charset.h
-- Installing: /usr/local/include/absl/strings/string_view.h
-- Installing: /usr/local/include/absl/flags
-- Installing: /usr/local/include/absl/flags/commandlineflag.h
-- Installing: /usr/local/include/absl/flags/usage_config.h
-- Installing: /usr/local/include/absl/flags/flag.h
-- Installing: /usr/local/include/absl/flags/config.h
-- Installing: /usr/local/include/absl/flags/declare.h
-- Installing: /usr/local/include/absl/flags/usage.h
-- Installing: /usr/local/include/absl/flags/reflection.h
-- Installing: /usr/local/include/absl/flags/internal
-- Installing: /usr/local/include/absl/flags/internal/commandlineflag.h
-- Installing: /usr/local/include/absl/flags/internal/flag.h
-- Installing: /usr/local/include/absl/flags/internal/program_name.h
-- Installing: /usr/local/include/absl/flags/internal/usage.h
-- Installing: /usr/local/include/absl/flags/internal/sequence_lock.h
-- Installing: /usr/local/include/absl/flags/internal/path_util.h
-- Installing: /usr/local/include/absl/flags/internal/registry.h
-- Installing: /usr/local/include/absl/flags/internal/private_handle_accessor.h
-- Installing: /usr/local/include/absl/flags/internal/parse.h
-- Installing: /usr/local/include/absl/flags/marshalling.h
-- Installing: /usr/local/include/absl/flags/parse.h
-- Installing: /usr/local/include/absl/cleanup
-- Installing: /usr/local/include/absl/cleanup/internal
-- Installing: /usr/local/include/absl/cleanup/internal/cleanup.h
-- Installing: /usr/local/include/absl/cleanup/cleanup.h
-- Installing: /usr/local/include/absl/log
-- Installing: /usr/local/include/absl/log/globals.h
-- Installing: /usr/local/include/absl/log/log_streamer.h
-- Installing: /usr/local/include/absl/log/die_if_null.h
-- Installing: /usr/local/include/absl/log/log_entry.h
-- Installing: /usr/local/include/absl/log/scoped_mock_log.h
-- Installing: /usr/local/include/absl/log/initialize.h
-- Installing: /usr/local/include/absl/log/log_sink_registry.h
-- Installing: /usr/local/include/absl/log/absl_log.h
-- Installing: /usr/local/include/absl/log/structured.h
-- Installing: /usr/local/include/absl/log/absl_check.h
-- Installing: /usr/local/include/absl/log/absl_vlog_is_on.h
-- Installing: /usr/local/include/absl/log/internal
-- Installing: /usr/local/include/absl/log/internal/test_helpers.h
-- Installing: /usr/local/include/absl/log/internal/append_truncated.h
-- Installing: /usr/local/include/absl/log/internal/globals.h
-- Installing: /usr/local/include/absl/log/internal/config.h
-- Installing: /usr/local/include/absl/log/internal/test_matchers.h
-- Installing: /usr/local/include/absl/log/internal/log_message.h
-- Installing: /usr/local/include/absl/log/internal/fnmatch.h
-- Installing: /usr/local/include/absl/log/internal/log_sink_set.h
-- Installing: /usr/local/include/absl/log/internal/structured.h
-- Installing: /usr/local/include/absl/log/internal/vlog_config.h
-- Installing: /usr/local/include/absl/log/internal/check_impl.h
-- Installing: /usr/local/include/absl/log/internal/conditions.h
-- Installing: /usr/local/include/absl/log/internal/nullstream.h
-- Installing: /usr/local/include/absl/log/internal/strip.h
-- Installing: /usr/local/include/absl/log/internal/test_actions.h
-- Installing: /usr/local/include/absl/log/internal/log_impl.h
-- Installing: /usr/local/include/absl/log/internal/flags.h
-- Installing: /usr/local/include/absl/log/internal/check_op.h
-- Installing: /usr/local/include/absl/log/internal/voidify.h
-- Installing: /usr/local/include/absl/log/internal/log_format.h
-- Installing: /usr/local/include/absl/log/internal/proto.h
-- Installing: /usr/local/include/absl/log/internal/nullguard.h
-- Installing: /usr/local/include/absl/log/log_sink.h
-- Installing: /usr/local/include/absl/log/flags.h
-- Installing: /usr/local/include/absl/log/log.h
-- Installing: /usr/local/include/absl/log/check.h
-- Installing: /usr/local/include/absl/log/log_basic_test_impl.inc
-- Installing: /usr/local/include/absl/log/vlog_is_on.h
-- Installing: /usr/local/include/absl/log/check_test_impl.inc
-- Installing: /usr/local/include/absl/numeric
-- Installing: /usr/local/include/absl/numeric/int128_no_intrinsic.inc
-- Installing: /usr/local/include/absl/numeric/int128_have_intrinsic.inc
-- Installing: /usr/local/include/absl/numeric/int128.h
-- Installing: /usr/local/include/absl/numeric/bits.h
-- Installing: /usr/local/include/absl/numeric/internal
-- Installing: /usr/local/include/absl/numeric/internal/bits.h
-- Installing: /usr/local/include/absl/numeric/internal/representation.h
-- Installing: /usr/local/include/absl/base
-- Installing: /usr/local/include/absl/base/options.h
-- Installing: /usr/local/include/absl/base/attributes.h
-- Installing: /usr/local/include/absl/base/macros.h
-- Installing: /usr/local/include/absl/base/config.h
-- Installing: /usr/local/include/absl/base/call_once.h
-- Installing: /usr/local/include/absl/base/nullability.h
-- Installing: /usr/local/include/absl/base/prefetch.h
-- Installing: /usr/local/include/absl/base/no_destructor.h
-- Installing: /usr/local/include/absl/base/policy_checks.h
-- Installing: /usr/local/include/absl/base/internal
-- Installing: /usr/local/include/absl/base/internal/scoped_set_env.h
-- Installing: /usr/local/include/absl/base/internal/spinlock_wait.h
-- Installing: /usr/local/include/absl/base/internal/nullability_impl.h
-- Installing: /usr/local/include/absl/base/internal/fast_type_id.h
-- Installing: /usr/local/include/absl/base/internal/direct_mmap.h
-- Installing: /usr/local/include/absl/base/internal/endian.h
-- Installing: /usr/local/include/absl/base/internal/exception_testing.h
-- Installing: /usr/local/include/absl/base/internal/atomic_hook.h
-- Installing: /usr/local/include/absl/base/internal/spinlock_akaros.inc
-- Installing: /usr/local/include/absl/base/internal/inline_variable_testing.h
-- Installing: /usr/local/include/absl/base/internal/inline_variable.h
-- Installing: /usr/local/include/absl/base/internal/exception_safety_testing.h
-- Installing: /usr/local/include/absl/base/internal/raw_logging.h
-- Installing: /usr/local/include/absl/base/internal/throw_delegate.h
-- Installing: /usr/local/include/absl/base/internal/unaligned_access.h
-- Installing: /usr/local/include/absl/base/internal/low_level_alloc.h
-- Installing: /usr/local/include/absl/base/internal/unscaledcycleclock_config.h
-- Installing: /usr/local/include/absl/base/internal/atomic_hook_test_helper.h
-- Installing: /usr/local/include/absl/base/internal/hide_ptr.h
-- Installing: /usr/local/include/absl/base/internal/per_thread_tls.h
-- Installing: /usr/local/include/absl/base/internal/tsan_mutex_interface.h
-- Installing: /usr/local/include/absl/base/internal/sysinfo.h
-- Installing: /usr/local/include/absl/base/internal/spinlock_win32.inc
-- Installing: /usr/local/include/absl/base/internal/scheduling_mode.h
-- Installing: /usr/local/include/absl/base/internal/spinlock.h
-- Installing: /usr/local/include/absl/base/internal/pretty_function.h
-- Installing: /usr/local/include/absl/base/internal/thread_identity.h
-- Installing: /usr/local/include/absl/base/internal/identity.h
-- Installing: /usr/local/include/absl/base/internal/errno_saver.h
-- Installing: /usr/local/include/absl/base/internal/spinlock_posix.inc
-- Installing: /usr/local/include/absl/base/internal/invoke.h
-- Installing: /usr/local/include/absl/base/internal/cycleclock.h
-- Installing: /usr/local/include/absl/base/internal/low_level_scheduling.h
-- Installing: /usr/local/include/absl/base/internal/cycleclock_config.h
-- Installing: /usr/local/include/absl/base/internal/unscaledcycleclock.h
-- Installing: /usr/local/include/absl/base/internal/spinlock_linux.inc
-- Installing: /usr/local/include/absl/base/internal/dynamic_annotations.h
-- Installing: /usr/local/include/absl/base/internal/strerror.h
-- Installing: /usr/local/include/absl/base/thread_annotations.h
-- Installing: /usr/local/include/absl/base/port.h
-- Installing: /usr/local/include/absl/base/casts.h
-- Installing: /usr/local/include/absl/base/log_severity.h
-- Installing: /usr/local/include/absl/base/const_init.h
-- Installing: /usr/local/include/absl/base/optimization.h
-- Installing: /usr/local/include/absl/base/dynamic_annotations.h
-- Installing: /usr/local/include/absl/random
-- Installing: /usr/local/include/absl/random/gaussian_distribution.h
-- Installing: /usr/local/include/absl/random/uniform_real_distribution.h
-- Installing: /usr/local/include/absl/random/bit_gen_ref.h
-- Installing: /usr/local/include/absl/random/distributions.h
-- Installing: /usr/local/include/absl/random/log_uniform_int_distribution.h
-- Installing: /usr/local/include/absl/random/exponential_distribution.h
-- Installing: /usr/local/include/absl/random/seed_gen_exception.h
-- Installing: /usr/local/include/absl/random/bernoulli_distribution.h
-- Installing: /usr/local/include/absl/random/mock_distributions.h
-- Installing: /usr/local/include/absl/random/discrete_distribution.h
-- Installing: /usr/local/include/absl/random/mocking_bit_gen.h
-- Installing: /usr/local/include/absl/random/seed_sequences.h
-- Installing: /usr/local/include/absl/random/poisson_distribution.h
-- Installing: /usr/local/include/absl/random/internal
-- Installing: /usr/local/include/absl/random/internal/iostream_state_saver.h
-- Installing: /usr/local/include/absl/random/internal/mock_overload_set.h
-- Installing: /usr/local/include/absl/random/internal/distribution_test_util.h
-- Installing: /usr/local/include/absl/random/internal/randen_traits.h
-- Installing: /usr/local/include/absl/random/internal/randen_hwaes.h
-- Installing: /usr/local/include/absl/random/internal/wide_multiply.h
-- Installing: /usr/local/include/absl/random/internal/explicit_seed_seq.h
-- Installing: /usr/local/include/absl/random/internal/sequence_urbg.h
-- Installing: /usr/local/include/absl/random/internal/randen_slow.h
-- Installing: /usr/local/include/absl/random/internal/randen_detect.h
-- Installing: /usr/local/include/absl/random/internal/fast_uniform_bits.h
-- Installing: /usr/local/include/absl/random/internal/nanobenchmark.h
-- Installing: /usr/local/include/absl/random/internal/fastmath.h
-- Installing: /usr/local/include/absl/random/internal/nonsecure_base.h
-- Installing: /usr/local/include/absl/random/internal/platform.h
-- Installing: /usr/local/include/absl/random/internal/chi_square.h
-- Installing: /usr/local/include/absl/random/internal/seed_material.h
-- Installing: /usr/local/include/absl/random/internal/pool_urbg.h
-- Installing: /usr/local/include/absl/random/internal/mock_helpers.h
-- Installing: /usr/local/include/absl/random/internal/randen_engine.h
-- Installing: /usr/local/include/absl/random/internal/randen.h
-- Installing: /usr/local/include/absl/random/internal/generate_real.h
-- Installing: /usr/local/include/absl/random/internal/distribution_caller.h
-- Installing: /usr/local/include/absl/random/internal/traits.h
-- Installing: /usr/local/include/absl/random/internal/salted_seed_seq.h
-- Installing: /usr/local/include/absl/random/internal/pcg_engine.h
-- Installing: /usr/local/include/absl/random/internal/uniform_helper.h
-- Installing: /usr/local/include/absl/random/uniform_int_distribution.h
-- Installing: /usr/local/include/absl/random/zipf_distribution.h
-- Installing: /usr/local/include/absl/random/random.h
-- Installing: /usr/local/include/absl/random/beta_distribution.h
-- Installing: /usr/local/include/absl/profiling
-- Installing: /usr/local/include/absl/profiling/internal
-- Installing: /usr/local/include/absl/profiling/internal/exponential_biased.h
-- Installing: /usr/local/include/absl/profiling/internal/periodic_sampler.h
-- Installing: /usr/local/include/absl/profiling/internal/sample_recorder.h
-- Installing: /usr/local/include/absl/types
-- Installing: /usr/local/include/absl/types/bad_variant_access.h
-- Installing: /usr/local/include/absl/types/any.h
-- Installing: /usr/local/include/absl/types/bad_optional_access.h
-- Installing: /usr/local/include/absl/types/optional.h
-- Installing: /usr/local/include/absl/types/span.h
-- Installing: /usr/local/include/absl/types/internal
-- Installing: /usr/local/include/absl/types/internal/optional.h
-- Installing: /usr/local/include/absl/types/internal/span.h
-- Installing: /usr/local/include/absl/types/internal/variant.h
-- Installing: /usr/local/include/absl/types/bad_any_cast.h
-- Installing: /usr/local/include/absl/types/variant.h
-- Installing: /usr/local/include/absl/types/compare.h
-- Installing: /usr/local/include/absl/meta
-- Installing: /usr/local/include/absl/meta/type_traits.h
-- Installing: /usr/local/include/absl/status
-- Installing: /usr/local/include/absl/status/status.h
-- Installing: /usr/local/include/absl/status/internal
-- Installing: /usr/local/include/absl/status/internal/status_internal.h
-- Installing: /usr/local/include/absl/status/internal/statusor_internal.h
-- Installing: /usr/local/include/absl/status/statusor.h
-- Installing: /usr/local/include/absl/status/status_payload_printer.h
-- Installing: /usr/local/include/absl/container
-- Installing: /usr/local/include/absl/container/btree_set.h
-- Installing: /usr/local/include/absl/container/fixed_array.h
-- Installing: /usr/local/include/absl/container/node_hash_set.h
-- Installing: /usr/local/include/absl/container/flat_hash_map.h
-- Installing: /usr/local/include/absl/container/btree_test.h
-- Installing: /usr/local/include/absl/container/btree_map.h
-- Installing: /usr/local/include/absl/container/internal
-- Installing: /usr/local/include/absl/container/internal/unordered_set_members_test.h
-- Installing: /usr/local/include/absl/container/internal/unordered_set_constructor_test.h
-- Installing: /usr/local/include/absl/container/internal/btree_container.h
-- Installing: /usr/local/include/absl/container/internal/hash_function_defaults.h
-- Installing: /usr/local/include/absl/container/internal/raw_hash_set.h
-- Installing: /usr/local/include/absl/container/internal/common.h
-- Installing: /usr/local/include/absl/container/internal/node_slot_policy.h
-- Installing: /usr/local/include/absl/container/internal/hashtable_debug_hooks.h
-- Installing: /usr/local/include/absl/container/internal/common_policy_traits.h
-- Installing: /usr/local/include/absl/container/internal/compressed_tuple.h
-- Installing: /usr/local/include/absl/container/internal/unordered_map_constructor_test.h
-- Installing: /usr/local/include/absl/container/internal/unordered_set_modifiers_test.h
-- Installing: /usr/local/include/absl/container/internal/hash_policy_testing.h
-- Installing: /usr/local/include/absl/container/internal/hashtable_debug.h
-- Installing: /usr/local/include/absl/container/internal/unordered_map_members_test.h
-- Installing: /usr/local/include/absl/container/internal/hashtablez_sampler.h
-- Installing: /usr/local/include/absl/container/internal/unordered_map_lookup_test.h
-- Installing: /usr/local/include/absl/container/internal/layout.h
-- Installing: /usr/local/include/absl/container/internal/container_memory.h
-- Installing: /usr/local/include/absl/container/internal/raw_hash_map.h
-- Installing: /usr/local/include/absl/container/internal/unordered_map_modifiers_test.h
-- Installing: /usr/local/include/absl/container/internal/btree.h
-- Installing: /usr/local/include/absl/container/internal/hash_generator_testing.h
-- Installing: /usr/local/include/absl/container/internal/unordered_set_lookup_test.h
-- Installing: /usr/local/include/absl/container/internal/tracked.h
-- Installing: /usr/local/include/absl/container/internal/test_instance_tracker.h
-- Installing: /usr/local/include/absl/container/internal/inlined_vector.h
-- Installing: /usr/local/include/absl/container/internal/test_allocator.h
-- Installing: /usr/local/include/absl/container/internal/hash_policy_traits.h
-- Installing: /usr/local/include/absl/container/flat_hash_set.h
-- Installing: /usr/local/include/absl/container/node_hash_map.h
-- Installing: /usr/local/include/absl/container/inlined_vector.h
-- Installing: /usr/local/include/absl/utility
-- Installing: /usr/local/include/absl/utility/utility.h
-- Installing: /usr/local/include/absl/utility/internal
-- Installing: /usr/local/include/absl/utility/internal/if_constexpr.h
-- Installing: /usr/local/include/absl/hash
-- Installing: /usr/local/include/absl/hash/hash_testing.h
-- Installing: /usr/local/include/absl/hash/internal
-- Installing: /usr/local/include/absl/hash/internal/low_level_hash.h
-- Installing: /usr/local/include/absl/hash/internal/city.h
-- Installing: /usr/local/include/absl/hash/internal/spy_hash_state.h
-- Installing: /usr/local/include/absl/hash/internal/hash.h
-- Installing: /usr/local/include/absl/hash/internal/hash_test.h
-- Installing: /usr/local/include/absl/hash/hash.h
-- Installing: /usr/local/include/absl/synchronization
-- Installing: /usr/local/include/absl/synchronization/blocking_counter.h
-- Installing: /usr/local/include/absl/synchronization/notification.h
-- Installing: /usr/local/include/absl/synchronization/internal
-- Installing: /usr/local/include/absl/synchronization/internal/pthread_waiter.h
-- Installing: /usr/local/include/absl/synchronization/internal/waiter_base.h
-- Installing: /usr/local/include/absl/synchronization/internal/stdcpp_waiter.h
-- Installing: /usr/local/include/absl/synchronization/internal/graphcycles.h
-- Installing: /usr/local/include/absl/synchronization/internal/futex_waiter.h
-- Installing: /usr/local/include/absl/synchronization/internal/per_thread_sem.h
-- Installing: /usr/local/include/absl/synchronization/internal/win32_waiter.h
-- Installing: /usr/local/include/absl/synchronization/internal/create_thread_identity.h
-- Installing: /usr/local/include/absl/synchronization/internal/kernel_timeout.h
-- Installing: /usr/local/include/absl/synchronization/internal/thread_pool.h
-- Installing: /usr/local/include/absl/synchronization/internal/sem_waiter.h
-- Installing: /usr/local/include/absl/synchronization/internal/waiter.h
-- Installing: /usr/local/include/absl/synchronization/internal/futex.h
-- Installing: /usr/local/include/absl/synchronization/mutex.h
-- Installing: /usr/local/include/absl/synchronization/barrier.h
-- Installing: /usr/local/include/eigen3
-- Installing: /usr/local/include/eigen3/signature_of_eigen3_matrix_library
-- Installing: /usr/local/include/eigen3/Eigen
-- Installing: /usr/local/include/eigen3/Eigen/Cholesky
-- Installing: /usr/local/include/eigen3/Eigen/Sparse
-- Installing: /usr/local/include/eigen3/Eigen/Eigenvalues
-- Installing: /usr/local/include/eigen3/Eigen/SparseCore
-- Installing: /usr/local/include/eigen3/Eigen/IterativeLinearSolvers
-- Installing: /usr/local/include/eigen3/Eigen/StdList
-- Installing: /usr/local/include/eigen3/Eigen/CholmodSupport
-- Installing: /usr/local/include/eigen3/Eigen/StdDeque
-- Installing: /usr/local/include/eigen3/Eigen/Geometry
-- Installing: /usr/local/include/eigen3/Eigen/Jacobi
-- Installing: /usr/local/include/eigen3/Eigen/KLUSupport
-- Installing: /usr/local/include/eigen3/Eigen/Eigen
-- Installing: /usr/local/include/eigen3/Eigen/SparseLU
-- Installing: /usr/local/include/eigen3/Eigen/MetisSupport
-- Installing: /usr/local/include/eigen3/Eigen/SPQRSupport
-- Installing: /usr/local/include/eigen3/Eigen/QtAlignedMalloc
-- Installing: /usr/local/include/eigen3/Eigen/Dense
-- Installing: /usr/local/include/eigen3/Eigen/Core
-- Installing: /usr/local/include/eigen3/Eigen/SuperLUSupport
-- Installing: /usr/local/include/eigen3/Eigen/Householder
-- Installing: /usr/local/include/eigen3/Eigen/StdVector
-- Installing: /usr/local/include/eigen3/Eigen/OrderingMethods
-- Installing: /usr/local/include/eigen3/Eigen/LU
-- Installing: /usr/local/include/eigen3/Eigen/src
-- Installing: /usr/local/include/eigen3/Eigen/src/Cholesky
-- Installing: /usr/local/include/eigen3/Eigen/src/Cholesky/LLT_LAPACKE.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Cholesky/LLT.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Cholesky/LDLT.h
-- Installing: /usr/local/include/eigen3/Eigen/src/StlSupport
-- Installing: /usr/local/include/eigen3/Eigen/src/StlSupport/details.h
-- Installing: /usr/local/include/eigen3/Eigen/src/StlSupport/StdVector.h
-- Installing: /usr/local/include/eigen3/Eigen/src/StlSupport/StdList.h
-- Installing: /usr/local/include/eigen3/Eigen/src/StlSupport/StdDeque.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Eigenvalues
-- Installing: /usr/local/include/eigen3/Eigen/src/Eigenvalues/ComplexSchur_LAPACKE.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Eigenvalues/RealQZ.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Eigenvalues/EigenSolver.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Eigenvalues/SelfAdjointEigenSolver.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Eigenvalues/SelfAdjointEigenSolver_LAPACKE.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Eigenvalues/Tridiagonalization.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Eigenvalues/GeneralizedSelfAdjointEigenSolver.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Eigenvalues/GeneralizedEigenSolver.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Eigenvalues/HessenbergDecomposition.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Eigenvalues/MatrixBaseEigenvalues.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Eigenvalues/RealSchur_LAPACKE.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Eigenvalues/ComplexSchur.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Eigenvalues/RealSchur.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Eigenvalues/ComplexEigenSolver.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseRef.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseMatrixBase.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseTranspose.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseDenseProduct.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseProduct.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseFuzzy.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseSparseProductWithPruning.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseVector.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseUtil.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/MappedSparseMatrix.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseMatrix.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/CompressedStorage.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/ConservativeSparseSparseProduct.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/AmbiVector.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparsePermutation.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseDiagonalProduct.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseAssign.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseDot.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseMap.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseTriangularView.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseColEtree.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseBlock.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseCwiseUnaryOp.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/TriangularSolver.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseSelfAdjointView.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseCwiseBinaryOp.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseRedux.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseView.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseCompressedBase.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCore/SparseSolverBase.h
-- Installing: /usr/local/include/eigen3/Eigen/src/IterativeLinearSolvers
-- Installing: /usr/local/include/eigen3/Eigen/src/IterativeLinearSolvers/BiCGSTAB.h
-- Installing: /usr/local/include/eigen3/Eigen/src/IterativeLinearSolvers/IncompleteCholesky.h
-- Installing: /usr/local/include/eigen3/Eigen/src/IterativeLinearSolvers/BasicPreconditioners.h
-- Installing: /usr/local/include/eigen3/Eigen/src/IterativeLinearSolvers/ConjugateGradient.h
-- Installing: /usr/local/include/eigen3/Eigen/src/IterativeLinearSolvers/IterativeSolverBase.h
-- Installing: /usr/local/include/eigen3/Eigen/src/IterativeLinearSolvers/SolveWithGuess.h
-- Installing: /usr/local/include/eigen3/Eigen/src/IterativeLinearSolvers/LeastSquareConjugateGradient.h
-- Installing: /usr/local/include/eigen3/Eigen/src/IterativeLinearSolvers/IncompleteLUT.h
-- Installing: /usr/local/include/eigen3/Eigen/src/plugins
-- Installing: /usr/local/include/eigen3/Eigen/src/plugins/BlockMethods.h
-- Installing: /usr/local/include/eigen3/Eigen/src/plugins/CommonCwiseUnaryOps.h
-- Installing: /usr/local/include/eigen3/Eigen/src/plugins/ArrayCwiseUnaryOps.h
-- Installing: /usr/local/include/eigen3/Eigen/src/plugins/MatrixCwiseBinaryOps.h
-- Installing: /usr/local/include/eigen3/Eigen/src/plugins/MatrixCwiseUnaryOps.h
-- Installing: /usr/local/include/eigen3/Eigen/src/plugins/IndexedViewMethods.h
-- Installing: /usr/local/include/eigen3/Eigen/src/plugins/ReshapedMethods.h
-- Installing: /usr/local/include/eigen3/Eigen/src/plugins/ArrayCwiseBinaryOps.h
-- Installing: /usr/local/include/eigen3/Eigen/src/plugins/CommonCwiseBinaryOps.h
-- Installing: /usr/local/include/eigen3/Eigen/src/CholmodSupport
-- Installing: /usr/local/include/eigen3/Eigen/src/CholmodSupport/CholmodSupport.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Geometry
-- Installing: /usr/local/include/eigen3/Eigen/src/Geometry/Umeyama.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Geometry/Translation.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Geometry/Hyperplane.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Geometry/arch
-- Installing: /usr/local/include/eigen3/Eigen/src/Geometry/arch/Geometry_SIMD.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Geometry/Homogeneous.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Geometry/RotationBase.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Geometry/Rotation2D.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Geometry/Scaling.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Geometry/EulerAngles.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Geometry/OrthoMethods.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Geometry/Transform.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Geometry/ParametrizedLine.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Geometry/Quaternion.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Geometry/AlignedBox.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Geometry/AngleAxis.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Jacobi
-- Installing: /usr/local/include/eigen3/Eigen/src/Jacobi/Jacobi.h
-- Installing: /usr/local/include/eigen3/Eigen/src/KLUSupport
-- Installing: /usr/local/include/eigen3/Eigen/src/KLUSupport/KLUSupport.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseLU
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseLU/SparseLU_column_bmod.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseLU/SparseLU_Utils.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseLU/SparseLU_relax_snode.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseLU/SparseLU_copy_to_ucol.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseLU/SparseLU_panel_dfs.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseLU/SparseLU_Memory.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseLU/SparseLU_SupernodalMatrix.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseLU/SparseLUImpl.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseLU/SparseLU_pruneL.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseLU/SparseLU_gemm_kernel.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseLU/SparseLU_column_dfs.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseLU/SparseLU.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseLU/SparseLU_Structs.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseLU/SparseLU_pivotL.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseLU/SparseLU_kernel_bmod.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseLU/SparseLU_heap_relax_snode.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseLU/SparseLU_panel_bmod.h
-- Installing: /usr/local/include/eigen3/Eigen/src/MetisSupport
-- Installing: /usr/local/include/eigen3/Eigen/src/MetisSupport/MetisSupport.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SPQRSupport
-- Installing: /usr/local/include/eigen3/Eigen/src/SPQRSupport/SuiteSparseQRSupport.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/ForceAlignedAccess.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/PlainObjectBase.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/CwiseNullaryOp.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/MatrixBase.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Random.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/PartialReduxEvaluator.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/ArrayBase.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/PermutationMatrix.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/DiagonalProduct.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Product.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/DenseBase.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Transpositions.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/ConditionEstimator.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Solve.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/StableNorm.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Block.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/TriangularMatrix.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/EigenBase.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/ProductEvaluators.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/SVE
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/SVE/TypeCasting.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/SVE/MathFunctions.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/SVE/PacketMath.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/SYCL
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/SYCL/SyclMemoryModel.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/SYCL/TypeCasting.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/SYCL/MathFunctions.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/SYCL/PacketMath.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/SYCL/InteropHeaders.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/CUDA
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/CUDA/Complex.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/ZVector
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/ZVector/Complex.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/ZVector/MathFunctions.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/ZVector/PacketMath.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/NEON
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/NEON/Complex.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/NEON/GeneralBlockPanelKernel.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/NEON/TypeCasting.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/NEON/MathFunctions.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/NEON/PacketMath.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/AVX512
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/AVX512/Complex.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/AVX512/TypeCasting.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/AVX512/MathFunctions.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/AVX512/PacketMath.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/GPU
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/GPU/TypeCasting.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/GPU/MathFunctions.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/GPU/PacketMath.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/Default
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/Default/ConjHelper.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/Default/Half.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/Default/GenericPacketMathFunctions.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/Default/GenericPacketMathFunctionsFwd.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/Default/BFloat16.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/Default/TypeCasting.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/Default/Settings.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/AVX
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/AVX/Complex.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/AVX/TypeCasting.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/AVX/MathFunctions.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/AVX/PacketMath.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/MSA
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/MSA/Complex.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/MSA/MathFunctions.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/MSA/PacketMath.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/HIP
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/HIP/hcc
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/HIP/hcc/math_constants.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/SSE
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/SSE/Complex.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/SSE/TypeCasting.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/SSE/MathFunctions.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/SSE/PacketMath.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/AltiVec
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/AltiVec/MatrixProductCommon.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/AltiVec/MatrixProduct.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/AltiVec/MatrixProductMMA.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/AltiVec/Complex.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/AltiVec/MathFunctions.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/arch/AltiVec/PacketMath.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/ArrayWrapper.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Redux.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Map.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/CoreIterators.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/GenericPacketMath.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/DenseCoeffsBase.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/functors
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/functors/NullaryFunctors.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/functors/BinaryFunctors.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/functors/AssignmentFunctors.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/functors/TernaryFunctors.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/functors/StlFunctors.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/functors/UnaryFunctors.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Dot.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/CommaInitializer.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Swap.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/SolverBase.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/VectorBlock.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Reverse.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Assign_MKL.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/AssignEvaluator.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Assign.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/SelfCwiseBinaryOp.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Diagonal.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Ref.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/util
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/util/XprHelper.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/util/Constants.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/util/ReenableStupidWarnings.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/util/ReshapedHelper.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/util/MKL_support.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/util/Macros.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/util/IndexedViewHelper.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/util/SymbolicIndex.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/util/IntegralConstant.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/util/StaticAssert.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/util/Memory.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/util/ConfigureVectorization.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/util/NonMPL2.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/util/BlasUtil.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/util/DisableStupidWarnings.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/util/Meta.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/util/ForwardDeclarations.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/CwiseUnaryView.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/DenseStorage.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/BandMatrix.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/BooleanRedux.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Transpose.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/GeneralMatrixVector.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/GeneralMatrixMatrixTriangular_BLAS.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/Parallelizer.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/SelfadjointMatrixMatrix_BLAS.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/SelfadjointMatrixVector_BLAS.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/TriangularMatrixMatrix_BLAS.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/GeneralBlockPanelKernel.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/SelfadjointMatrixVector.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/SelfadjointRank2Update.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/SelfadjointProduct.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/GeneralMatrixMatrix.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/TriangularMatrixMatrix.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/SelfadjointMatrixMatrix.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/GeneralMatrixMatrix_BLAS.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/TriangularSolverVector.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/GeneralMatrixMatrixTriangular.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/GeneralMatrixVector_BLAS.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/TriangularMatrixVector.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/TriangularMatrixVector_BLAS.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/TriangularSolverMatrix.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/products/TriangularSolverMatrix_BLAS.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/GeneralProduct.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Fuzzy.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/NumTraits.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/StlIterators.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/ArithmeticSequence.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/SelfAdjointView.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Matrix.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Stride.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/MathFunctionsImpl.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Reshaped.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/IndexedView.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/VectorwiseOp.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Select.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/CwiseBinaryOp.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/MathFunctions.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/MapBase.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/CoreEvaluators.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/NoAlias.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Inverse.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/CwiseTernaryOp.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/DiagonalMatrix.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/ReturnByValue.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Visitor.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/CwiseUnaryOp.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Array.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/NestByValue.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/SolveTriangular.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/IO.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/Replicate.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Core/GlobalFunctions.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SuperLUSupport
-- Installing: /usr/local/include/eigen3/Eigen/src/SuperLUSupport/SuperLUSupport.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Householder
-- Installing: /usr/local/include/eigen3/Eigen/src/Householder/BlockHouseholder.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Householder/Householder.h
-- Installing: /usr/local/include/eigen3/Eigen/src/Householder/HouseholderSequence.h
-- Installing: /usr/local/include/eigen3/Eigen/src/OrderingMethods
-- Installing: /usr/local/include/eigen3/Eigen/src/OrderingMethods/Ordering.h
-- Installing: /usr/local/include/eigen3/Eigen/src/OrderingMethods/Eigen_Colamd.h
-- Installing: /usr/local/include/eigen3/Eigen/src/OrderingMethods/Amd.h
-- Installing: /usr/local/include/eigen3/Eigen/src/LU
-- Installing: /usr/local/include/eigen3/Eigen/src/LU/Determinant.h
-- Installing: /usr/local/include/eigen3/Eigen/src/LU/InverseImpl.h
-- Installing: /usr/local/include/eigen3/Eigen/src/LU/arch
-- Installing: /usr/local/include/eigen3/Eigen/src/LU/arch/InverseSize4.h
-- Installing: /usr/local/include/eigen3/Eigen/src/LU/PartialPivLU_LAPACKE.h
-- Installing: /usr/local/include/eigen3/Eigen/src/LU/FullPivLU.h
-- Installing: /usr/local/include/eigen3/Eigen/src/LU/PartialPivLU.h
-- Installing: /usr/local/include/eigen3/Eigen/src/QR
-- Installing: /usr/local/include/eigen3/Eigen/src/QR/HouseholderQR.h
-- Installing: /usr/local/include/eigen3/Eigen/src/QR/FullPivHouseholderQR.h
-- Installing: /usr/local/include/eigen3/Eigen/src/QR/ColPivHouseholderQR_LAPACKE.h
-- Installing: /usr/local/include/eigen3/Eigen/src/QR/ColPivHouseholderQR.h
-- Installing: /usr/local/include/eigen3/Eigen/src/QR/CompleteOrthogonalDecomposition.h
-- Installing: /usr/local/include/eigen3/Eigen/src/QR/HouseholderQR_LAPACKE.h
-- Installing: /usr/local/include/eigen3/Eigen/src/PaStiXSupport
-- Installing: /usr/local/include/eigen3/Eigen/src/PaStiXSupport/PaStiXSupport.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SVD
-- Installing: /usr/local/include/eigen3/Eigen/src/SVD/JacobiSVD.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SVD/BDCSVD.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SVD/SVDBase.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SVD/UpperBidiagonalization.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SVD/JacobiSVD_LAPACKE.h
-- Installing: /usr/local/include/eigen3/Eigen/src/UmfPackSupport
-- Installing: /usr/local/include/eigen3/Eigen/src/UmfPackSupport/UmfPackSupport.h
-- Installing: /usr/local/include/eigen3/Eigen/src/PardisoSupport
-- Installing: /usr/local/include/eigen3/Eigen/src/PardisoSupport/PardisoSupport.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCholesky
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCholesky/SimplicialCholesky.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseCholesky/SimplicialCholesky_impl.h
-- Installing: /usr/local/include/eigen3/Eigen/src/misc
-- Installing: /usr/local/include/eigen3/Eigen/src/misc/lapack.h
-- Installing: /usr/local/include/eigen3/Eigen/src/misc/lapacke.h
-- Installing: /usr/local/include/eigen3/Eigen/src/misc/lapacke_mangling.h
-- Installing: /usr/local/include/eigen3/Eigen/src/misc/RealSvd2x2.h
-- Installing: /usr/local/include/eigen3/Eigen/src/misc/Kernel.h
-- Installing: /usr/local/include/eigen3/Eigen/src/misc/Image.h
-- Installing: /usr/local/include/eigen3/Eigen/src/misc/blas.h
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseQR
-- Installing: /usr/local/include/eigen3/Eigen/src/SparseQR/SparseQR.h
-- Installing: /usr/local/include/eigen3/Eigen/QR
-- Installing: /usr/local/include/eigen3/Eigen/PaStiXSupport
-- Installing: /usr/local/include/eigen3/Eigen/SVD
-- Installing: /usr/local/include/eigen3/Eigen/UmfPackSupport
-- Installing: /usr/local/include/eigen3/Eigen/PardisoSupport
-- Installing: /usr/local/include/eigen3/Eigen/SparseCholesky
-- Installing: /usr/local/include/eigen3/Eigen/SparseQR
-- Installing: /usr/local/include/eigen3/unsupported
-- Installing: /usr/local/include/eigen3/unsupported/Eigen
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/IterativeSolvers
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/Splines
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/SparseExtra
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/ArpackSupport
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/NumericalDiff
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/KroneckerProduct
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/Polynomials
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/BVH
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/AdolcForward
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/AlignedVector3
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/MoreVectorization
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/OpenGLSupport
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/LevenbergMarquardt
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/ThreadPool
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/TensorSymmetry
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/ThreadPool
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/ThreadPool/ThreadEnvironment.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/ThreadPool/RunQueue.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/ThreadPool/Barrier.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/ThreadPool/ThreadLocal.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/ThreadPool/ThreadCancel.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/ThreadPool/ThreadYield.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/ThreadPool/ThreadPoolInterface.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/ThreadPool/EventCount.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/ThreadPool/NonBlockingThreadPool.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/util
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/util/MaxSizeVector.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/util/CXX11Workarounds.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/util/EmulateArray.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/util/CXX11Meta.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/TensorSymmetry
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/TensorSymmetry/StaticSymmetry.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/TensorSymmetry/Symmetry.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/TensorSymmetry/DynamicSymmetry.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/TensorSymmetry/util
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/TensorSymmetry/util/TemplateGroupTheory.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorVolumePatch.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorTrace.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorGenerator.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorForcedEval.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/Tensor.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorArgMax.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorScan.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorGpuHipCudaDefines.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorDeviceDefault.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorDimensionList.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorDeviceCuda.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorRef.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorMorphing.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorCostModel.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorPadding.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorMacros.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorInitializer.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorEvalTo.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorReductionCuda.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorAssign.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorConvolutionSycl.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorScanSycl.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorFixedSize.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorReverse.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorFFT.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorForwardDeclarations.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorMap.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorCustomOp.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorConvolution.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorIndexList.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorRandom.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorContractionCuda.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorBase.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorUInt128.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorLayoutSwap.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorBlock.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorIntDiv.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorReductionGpu.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorDevice.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorReductionSycl.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorExecutor.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorConversion.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorStorage.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorContraction.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorDeviceSycl.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorChipping.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorFunctors.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorReduction.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorMeta.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorEvaluator.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorDeviceGpu.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorConcatenation.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorDeviceThreadPool.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorInflation.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorExpr.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorContractionBlocking.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorIO.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorBroadcasting.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorContractionMapper.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorPatch.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorContractionGpu.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorContractionSycl.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorShuffling.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorContractionThreadPool.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorImagePatch.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorGlobalFunctions.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorStriding.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorGpuHipCudaUndefines.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorDimensions.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/src/Tensor/TensorTraits.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/CXX11/Tensor
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/MatrixFunctions
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/SpecialFunctions
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/FFT
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/Skyline
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/IterativeSolvers
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/IterativeSolvers/MINRES.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/IterativeSolvers/IncompleteLU.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/IterativeSolvers/GMRES.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/IterativeSolvers/Scaling.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/IterativeSolvers/ConstrainedConjGrad.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/IterativeSolvers/IterationController.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/IterativeSolvers/DGMRES.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/IterativeSolvers/IDRS.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/Splines
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/Splines/SplineFitting.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/Splines/SplineFwd.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/Splines/Spline.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SparseExtra
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SparseExtra/BlockOfDynamicSparseMatrix.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SparseExtra/DynamicSparseMatrix.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SparseExtra/MatrixMarketIterator.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SparseExtra/MarketIO.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SparseExtra/BlockSparseMatrix.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SparseExtra/RandomSetter.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/Eigenvalues
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/Eigenvalues/ArpackSelfAdjointEigenSolver.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/NumericalDiff
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/NumericalDiff/NumericalDiff.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/KroneckerProduct
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/KroneckerProduct/KroneckerTensorProduct.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/Polynomials
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/Polynomials/Companion.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/Polynomials/PolynomialUtils.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/Polynomials/PolynomialSolver.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/BVH
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/BVH/BVAlgorithms.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/BVH/KdBVH.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/MoreVectorization
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/MoreVectorization/MathFunctions.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/LevenbergMarquardt
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/LevenbergMarquardt/LMpar.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/LevenbergMarquardt/LevenbergMarquardt.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/LevenbergMarquardt/LMqrsolv.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/LevenbergMarquardt/LMcovar.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/LevenbergMarquardt/LMonestep.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/MatrixFunctions
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/MatrixFunctions/MatrixSquareRoot.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/MatrixFunctions/StemFunction.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/MatrixFunctions/MatrixLogarithm.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/MatrixFunctions/MatrixPower.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/MatrixFunctions/MatrixFunction.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/MatrixFunctions/MatrixExponential.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/BesselFunctionsFunctors.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/SpecialFunctionsPacketMath.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/BesselFunctionsArrayAPI.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/arch
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/arch/NEON
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/arch/NEON/BesselFunctions.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/arch/NEON/SpecialFunctions.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/arch/AVX512
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/arch/AVX512/BesselFunctions.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/arch/AVX512/SpecialFunctions.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/arch/GPU
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/arch/GPU/SpecialFunctions.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/arch/AVX
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/arch/AVX/BesselFunctions.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/arch/AVX/SpecialFunctions.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/HipVectorCompatibility.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/SpecialFunctionsArrayAPI.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/SpecialFunctionsHalf.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/BesselFunctionsPacketMath.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/SpecialFunctionsFunctors.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/BesselFunctionsBFloat16.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/SpecialFunctionsImpl.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/BesselFunctionsImpl.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/SpecialFunctionsBFloat16.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/SpecialFunctions/BesselFunctionsHalf.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/FFT
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/FFT/ei_fftw_impl.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/FFT/ei_kissfft_impl.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/Skyline
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/Skyline/SkylineUtil.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/Skyline/SkylineMatrixBase.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/Skyline/SkylineProduct.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/Skyline/SkylineMatrix.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/Skyline/SkylineInplaceLU.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/Skyline/SkylineStorage.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/AutoDiff
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/AutoDiff/AutoDiffScalar.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/AutoDiff/AutoDiffJacobian.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/AutoDiff/AutoDiffVector.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/EulerAngles
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/EulerAngles/EulerSystem.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/EulerAngles/EulerAngles.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/NonLinearOptimization
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/NonLinearOptimization/chkder.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/NonLinearOptimization/LevenbergMarquardt.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/NonLinearOptimization/rwupdt.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/NonLinearOptimization/r1updt.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/NonLinearOptimization/qrsolv.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/NonLinearOptimization/covar.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/NonLinearOptimization/lmpar.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/NonLinearOptimization/fdjac1.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/NonLinearOptimization/HybridNonLinearSolver.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/NonLinearOptimization/r1mpyq.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/src/NonLinearOptimization/dogleg.h
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/AutoDiff
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/EulerAngles
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/MPRealSupport
-- Installing: /usr/local/include/eigen3/unsupported/Eigen/NonLinearOptimization
-- Installing: /usr/local/include/ortools_export.h
-- Installing: /usr/local/include/utf8_range.h
-- Installing: /usr/local/include/google
-- Installing: /usr/local/include/google/protobuf
-- Installing: /usr/local/include/google/protobuf/feature_resolver.h
-- Installing: /usr/local/include/google/protobuf/type.proto
-- Installing: /usr/local/include/google/protobuf/api.proto
-- Installing: /usr/local/include/google/protobuf/map_field_lite.h
-- Installing: /usr/local/include/google/protobuf/generated_message_util.h
-- Installing: /usr/local/include/google/protobuf/implicit_weak_message.h
-- Installing: /usr/local/include/google/protobuf/generated_enum_reflection.h
-- Installing: /usr/local/include/google/protobuf/duration.proto
-- Installing: /usr/local/include/google/protobuf/thread_safe_arena.h
-- Installing: /usr/local/include/google/protobuf/empty.pb.h
-- Installing: /usr/local/include/google/protobuf/stubs
-- Installing: /usr/local/include/google/protobuf/stubs/common.h
-- Installing: /usr/local/include/google/protobuf/stubs/status_macros.h
-- Installing: /usr/local/include/google/protobuf/stubs/port.h
-- Installing: /usr/local/include/google/protobuf/stubs/platform_macros.h
-- Installing: /usr/local/include/google/protobuf/stubs/callback.h
-- Installing: /usr/local/include/google/protobuf/arenastring.h
-- Installing: /usr/local/include/google/protobuf/field_mask.pb.h
-- Installing: /usr/local/include/google/protobuf/unknown_field_set.h
-- Installing: /usr/local/include/google/protobuf/generated_message_bases.h
-- Installing: /usr/local/include/google/protobuf/arena_allocation_policy.h
-- Installing: /usr/local/include/google/protobuf/duration.pb.h
-- Installing: /usr/local/include/google/protobuf/repeated_field.h
-- Installing: /usr/local/include/google/protobuf/endian.h
-- Installing: /usr/local/include/google/protobuf/descriptor.h
-- Installing: /usr/local/include/google/protobuf/timestamp.pb.h
-- Installing: /usr/local/include/google/protobuf/cpp_features.pb.h
-- Installing: /usr/local/include/google/protobuf/descriptor_legacy.h
-- Installing: /usr/local/include/google/protobuf/service.h
-- Installing: /usr/local/include/google/protobuf/raw_ptr.h
-- Installing: /usr/local/include/google/protobuf/any.h
-- Installing: /usr/local/include/google/protobuf/reflection_ops.h
-- Installing: /usr/local/include/google/protobuf/cpp_features.proto
-- Installing: /usr/local/include/google/protobuf/text_format.h
-- Installing: /usr/local/include/google/protobuf/any.pb.h
-- Installing: /usr/local/include/google/protobuf/arena.h
-- Installing: /usr/local/include/google/protobuf/reflection_internal.h
-- Installing: /usr/local/include/google/protobuf/field_access_listener.h
-- Installing: /usr/local/include/google/protobuf/message.h
-- Installing: /usr/local/include/google/protobuf/descriptor_database.h
-- Installing: /usr/local/include/google/protobuf/serial_arena.h
-- Installing: /usr/local/include/google/protobuf/internal_visibility.h
-- Installing: /usr/local/include/google/protobuf/port_undef.inc
-- Installing: /usr/local/include/google/protobuf/type.pb.h
-- Installing: /usr/local/include/google/protobuf/source_context.pb.h
-- Installing: /usr/local/include/google/protobuf/map_field.h
-- Installing: /usr/local/include/google/protobuf/source_context.proto
-- Installing: /usr/local/include/google/protobuf/descriptor.proto
-- Installing: /usr/local/include/google/protobuf/map_entry.h
-- Installing: /usr/local/include/google/protobuf/inlined_string_field.h
-- Installing: /usr/local/include/google/protobuf/map_field_inl.h
-- Installing: /usr/local/include/google/protobuf/cpp_edition_defaults.h
-- Installing: /usr/local/include/google/protobuf/reflection.h
-- Installing: /usr/local/include/google/protobuf/json
-- Installing: /usr/local/include/google/protobuf/json/internal
-- Installing: /usr/local/include/google/protobuf/json/internal/descriptor_traits.h
-- Installing: /usr/local/include/google/protobuf/json/internal/unparser_traits.h
-- Installing: /usr/local/include/google/protobuf/json/internal/unparser.h
-- Installing: /usr/local/include/google/protobuf/json/internal/message_path.h
-- Installing: /usr/local/include/google/protobuf/json/internal/parser.h
-- Installing: /usr/local/include/google/protobuf/json/internal/untyped_message.h
-- Installing: /usr/local/include/google/protobuf/json/internal/zero_copy_buffered_stream.h
-- Installing: /usr/local/include/google/protobuf/json/internal/lexer.h
-- Installing: /usr/local/include/google/protobuf/json/internal/parser_traits.h
-- Installing: /usr/local/include/google/protobuf/json/internal/writer.h
-- Installing: /usr/local/include/google/protobuf/json/json.h
-- Installing: /usr/local/include/google/protobuf/descriptor_visitor.h
-- Installing: /usr/local/include/google/protobuf/reflection_mode.h
-- Installing: /usr/local/include/google/protobuf/dynamic_message.h
-- Installing: /usr/local/include/google/protobuf/wire_format.h
-- Installing: /usr/local/include/google/protobuf/util
-- Installing: /usr/local/include/google/protobuf/util/type_resolver_util.h
-- Installing: /usr/local/include/google/protobuf/util/time_util.h
-- Installing: /usr/local/include/google/protobuf/util/field_comparator.h
-- Installing: /usr/local/include/google/protobuf/util/message_differencer.h
-- Installing: /usr/local/include/google/protobuf/util/json_util.h
-- Installing: /usr/local/include/google/protobuf/util/type_resolver.h
-- Installing: /usr/local/include/google/protobuf/util/field_mask_util.h
-- Installing: /usr/local/include/google/protobuf/util/delimited_message_util.h
-- Installing: /usr/local/include/google/protobuf/arena_cleanup.h
-- Installing: /usr/local/include/google/protobuf/string_block.h
-- Installing: /usr/local/include/google/protobuf/compiler
-- Installing: /usr/local/include/google/protobuf/compiler/retention.h
-- Installing: /usr/local/include/google/protobuf/compiler/objectivec
-- Installing: /usr/local/include/google/protobuf/compiler/objectivec/line_consumer.h
-- Installing: /usr/local/include/google/protobuf/compiler/objectivec/options.h
-- Installing: /usr/local/include/google/protobuf/compiler/objectivec/message.h
-- Installing: /usr/local/include/google/protobuf/compiler/objectivec/map_field.h
-- Installing: /usr/local/include/google/protobuf/compiler/objectivec/file.h
-- Installing: /usr/local/include/google/protobuf/compiler/objectivec/primitive_field.h
-- Installing: /usr/local/include/google/protobuf/compiler/objectivec/oneof.h
-- Installing: /usr/local/include/google/protobuf/compiler/objectivec/message_field.h
-- Installing: /usr/local/include/google/protobuf/compiler/objectivec/enum.h
-- Installing: /usr/local/include/google/protobuf/compiler/objectivec/generator.h
-- Installing: /usr/local/include/google/protobuf/compiler/objectivec/extension.h
-- Installing: /usr/local/include/google/protobuf/compiler/objectivec/nsobject_methods.h
-- Installing: /usr/local/include/google/protobuf/compiler/objectivec/enum_field.h
-- Installing: /usr/local/include/google/protobuf/compiler/objectivec/import_writer.h
-- Installing: /usr/local/include/google/protobuf/compiler/objectivec/text_format_decode_data.h
-- Installing: /usr/local/include/google/protobuf/compiler/objectivec/helpers.h
-- Installing: /usr/local/include/google/protobuf/compiler/objectivec/field.h
-- Installing: /usr/local/include/google/protobuf/compiler/objectivec/names.h
-- Installing: /usr/local/include/google/protobuf/compiler/plugin.pb.h
-- Installing: /usr/local/include/google/protobuf/compiler/allowlists
-- Installing: /usr/local/include/google/protobuf/compiler/allowlists/allowlists.h
-- Installing: /usr/local/include/google/protobuf/compiler/allowlists/allowlist.h
-- Installing: /usr/local/include/google/protobuf/compiler/versions_suffix.h
-- Installing: /usr/local/include/google/protobuf/compiler/code_generator.h
-- Installing: /usr/local/include/google/protobuf/compiler/parser.h
-- Installing: /usr/local/include/google/protobuf/compiler/command_line_interface.h
-- Installing: /usr/local/include/google/protobuf/compiler/plugin.h
-- Installing: /usr/local/include/google/protobuf/compiler/scc.h
-- Installing: /usr/local/include/google/protobuf/compiler/subprocess.h
-- Installing: /usr/local/include/google/protobuf/compiler/csharp
-- Installing: /usr/local/include/google/protobuf/compiler/csharp/csharp_message_field.h
-- Installing: /usr/local/include/google/protobuf/compiler/csharp/csharp_field_base.h
-- Installing: /usr/local/include/google/protobuf/compiler/csharp/csharp_repeated_primitive_field.h
-- Installing: /usr/local/include/google/protobuf/compiler/csharp/csharp_repeated_enum_field.h
-- Installing: /usr/local/include/google/protobuf/compiler/csharp/csharp_helpers.h
-- Installing: /usr/local/include/google/protobuf/compiler/csharp/csharp_doc_comment.h
-- Installing: /usr/local/include/google/protobuf/compiler/csharp/csharp_source_generator_base.h
-- Installing: /usr/local/include/google/protobuf/compiler/csharp/csharp_enum.h
-- Installing: /usr/local/include/google/protobuf/compiler/csharp/csharp_enum_field.h
-- Installing: /usr/local/include/google/protobuf/compiler/csharp/csharp_repeated_message_field.h
-- Installing: /usr/local/include/google/protobuf/compiler/csharp/csharp_options.h
-- Installing: /usr/local/include/google/protobuf/compiler/csharp/csharp_primitive_field.h
-- Installing: /usr/local/include/google/protobuf/compiler/csharp/csharp_reflection_class.h
-- Installing: /usr/local/include/google/protobuf/compiler/csharp/csharp_wrapper_field.h
-- Installing: /usr/local/include/google/protobuf/compiler/csharp/csharp_generator.h
-- Installing: /usr/local/include/google/protobuf/compiler/csharp/csharp_message.h
-- Installing: /usr/local/include/google/protobuf/compiler/csharp/csharp_map_field.h
-- Installing: /usr/local/include/google/protobuf/compiler/csharp/names.h
-- Installing: /usr/local/include/google/protobuf/compiler/python
-- Installing: /usr/local/include/google/protobuf/compiler/python/pyi_generator.h
-- Installing: /usr/local/include/google/protobuf/compiler/python/generator.h
-- Installing: /usr/local/include/google/protobuf/compiler/python/helpers.h
-- Installing: /usr/local/include/google/protobuf/compiler/php
-- Installing: /usr/local/include/google/protobuf/compiler/php/php_generator.h
-- Installing: /usr/local/include/google/protobuf/compiler/php/names.h
-- Installing: /usr/local/include/google/protobuf/compiler/java
-- Installing: /usr/local/include/google/protobuf/compiler/java/string_field_lite.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/map_field_lite.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/options.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/shared_code_generator.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/message_builder.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/enum_field_lite.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/primitive_field_lite.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/doc_comment.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/enum_lite.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/service.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/message_field_lite.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/message.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/name_resolver.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/generator_factory.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/map_field.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/file.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/primitive_field.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/message_field.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/kotlin_generator.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/java_features.pb.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/message_lite.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/enum.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/generator.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/string_field.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/context.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/extension.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/enum_field.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/message_builder_lite.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/helpers.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/extension_lite.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/message_serialization.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/field.h
-- Installing: /usr/local/include/google/protobuf/compiler/java/names.h
-- Installing: /usr/local/include/google/protobuf/compiler/rust
-- Installing: /usr/local/include/google/protobuf/compiler/rust/message.h
-- Installing: /usr/local/include/google/protobuf/compiler/rust/oneof.h
-- Installing: /usr/local/include/google/protobuf/compiler/rust/relative_path.h
-- Installing: /usr/local/include/google/protobuf/compiler/rust/generator.h
-- Installing: /usr/local/include/google/protobuf/compiler/rust/context.h
-- Installing: /usr/local/include/google/protobuf/compiler/rust/accessors
-- Installing: /usr/local/include/google/protobuf/compiler/rust/accessors/accessors.h
-- Installing: /usr/local/include/google/protobuf/compiler/rust/accessors/accessor_generator.h
-- Installing: /usr/local/include/google/protobuf/compiler/rust/naming.h
-- Installing: /usr/local/include/google/protobuf/compiler/ruby
-- Installing: /usr/local/include/google/protobuf/compiler/ruby/ruby_generator.h
-- Installing: /usr/local/include/google/protobuf/compiler/zip_writer.h
-- Installing: /usr/local/include/google/protobuf/compiler/plugin.proto
-- Installing: /usr/local/include/google/protobuf/compiler/cpp
-- Installing: /usr/local/include/google/protobuf/compiler/cpp/options.h
-- Installing: /usr/local/include/google/protobuf/compiler/cpp/tracker.h
-- Installing: /usr/local/include/google/protobuf/compiler/cpp/service.h
-- Installing: /usr/local/include/google/protobuf/compiler/cpp/parse_function_generator.h
-- Installing: /usr/local/include/google/protobuf/compiler/cpp/message.h
-- Installing: /usr/local/include/google/protobuf/compiler/cpp/file.h
-- Installing: /usr/local/include/google/protobuf/compiler/cpp/field_generators
-- Installing: /usr/local/include/google/protobuf/compiler/cpp/field_generators/generators.h
-- Installing: /usr/local/include/google/protobuf/compiler/cpp/padding_optimizer.h
-- Installing: /usr/local/include/google/protobuf/compiler/cpp/message_layout_helper.h
-- Installing: /usr/local/include/google/protobuf/compiler/cpp/enum.h
-- Installing: /usr/local/include/google/protobuf/compiler/cpp/generator.h
-- Installing: /usr/local/include/google/protobuf/compiler/cpp/extension.h
-- Installing: /usr/local/include/google/protobuf/compiler/cpp/helpers.h
-- Installing: /usr/local/include/google/protobuf/compiler/cpp/field.h
-- Installing: /usr/local/include/google/protobuf/compiler/cpp/names.h
-- Installing: /usr/local/include/google/protobuf/compiler/versions.h
-- Installing: /usr/local/include/google/protobuf/compiler/importer.h
-- Installing: /usr/local/include/google/protobuf/explicitly_constructed.h
-- Installing: /usr/local/include/google/protobuf/any.proto
-- Installing: /usr/local/include/google/protobuf/message_lite.h
-- Installing: /usr/local/include/google/protobuf/extension_set.h
-- Installing: /usr/local/include/google/protobuf/map_type_handler.h
-- Installing: /usr/local/include/google/protobuf/wrappers.pb.h
-- Installing: /usr/local/include/google/protobuf/api.pb.h
-- Installing: /usr/local/include/google/protobuf/varint_shuffle.h
-- Installing: /usr/local/include/google/protobuf/generated_message_tctable_gen.h
-- Installing: /usr/local/include/google/protobuf/wrappers.proto
-- Installing: /usr/local/include/google/protobuf/port.h
-- Installing: /usr/local/include/google/protobuf/descriptor.pb.h
-- Installing: /usr/local/include/google/protobuf/repeated_ptr_field.h
-- Installing: /usr/local/include/google/protobuf/has_bits.h
-- Installing: /usr/local/include/google/protobuf/metadata_lite.h
-- Installing: /usr/local/include/google/protobuf/parse_context.h
-- Installing: /usr/local/include/google/protobuf/wire_format_lite.h
-- Installing: /usr/local/include/google/protobuf/generated_message_tctable_decl.h
-- Installing: /usr/local/include/google/protobuf/struct.proto
-- Installing: /usr/local/include/google/protobuf/extension_set_inl.h
-- Installing: /usr/local/include/google/protobuf/generated_message_tctable_impl.h
-- Installing: /usr/local/include/google/protobuf/map.h
-- Installing: /usr/local/include/google/protobuf/metadata.h
-- Installing: /usr/local/include/google/protobuf/internal_message_util.h
-- Installing: /usr/local/include/google/protobuf/timestamp.proto
-- Installing: /usr/local/include/google/protobuf/io
-- Installing: /usr/local/include/google/protobuf/io/io_win32.h
-- Installing: /usr/local/include/google/protobuf/io/printer.h
-- Installing: /usr/local/include/google/protobuf/io/zero_copy_stream.h
-- Installing: /usr/local/include/google/protobuf/io/zero_copy_sink.h
-- Installing: /usr/local/include/google/protobuf/io/zero_copy_stream_impl.h
-- Installing: /usr/local/include/google/protobuf/io/tokenizer.h
-- Installing: /usr/local/include/google/protobuf/io/zero_copy_stream_impl_lite.h
-- Installing: /usr/local/include/google/protobuf/io/strtod.h
-- Installing: /usr/local/include/google/protobuf/io/coded_stream.h
-- Installing: /usr/local/include/google/protobuf/io/gzip_stream.h
-- Installing: /usr/local/include/google/protobuf/generated_enum_util.h
-- Installing: /usr/local/include/google/protobuf/port_def.inc
-- Installing: /usr/local/include/google/protobuf/arena_align.h
-- Installing: /usr/local/include/google/protobuf/arenaz_sampler.h
-- Installing: /usr/local/include/google/protobuf/generated_message_reflection.h
-- Installing: /usr/local/include/google/protobuf/struct.pb.h
-- Installing: /usr/local/include/google/protobuf/empty.proto
-- Installing: /usr/local/include/google/protobuf/field_mask.proto
-- Installing: /usr/local/include/java
-- Installing: /usr/local/include/java/core
-- Installing: /usr/local/include/java/core/src
-- Installing: /usr/local/include/java/core/src/main
-- Installing: /usr/local/include/java/core/src/main/java
-- Installing: /usr/local/include/java/core/src/main/java/com
-- Installing: /usr/local/include/java/core/src/main/java/com/google
-- Installing: /usr/local/include/java/core/src/main/java/com/google/protobuf
-- Installing: /usr/local/include/java/core/src/main/java/com/google/protobuf/java_features.proto
-- Installing: /usr/local/include/coin
-- Installing: /usr/local/include/coin/CoinParam.hpp
-- Installing: /usr/local/include/coin/ClpInterior.hpp
-- Installing: /usr/local/include/coin/CbcHeuristicDiveFractional.hpp
-- Installing: /usr/local/include/coin/CbcObject.hpp
-- Installing: /usr/local/include/coin/MyMessageHandler.hpp
-- Installing: /usr/local/include/coin/ClpCholeskyDense.hpp
-- Installing: /usr/local/include/coin/CbcCompareBase.hpp
-- Installing: /usr/local/include/coin/CbcHeuristicLocal.hpp
-- Installing: /usr/local/include/coin/ClpPrimalColumnPivot.hpp
-- Installing: /usr/local/include/coin/ClpParameters.hpp
-- Installing: /usr/local/include/coin/CglClique.hpp
-- Installing: /usr/local/include/coin/CbcCompareActual.hpp
-- Installing: /usr/local/include/coin/CglZeroHalf.hpp
-- Installing: /usr/local/include/coin/CbcBranchLotsize.hpp
-- Installing: /usr/local/include/coin/CglMessage.hpp
-- Installing: /usr/local/include/coin/CglPreProcess.hpp
-- Installing: /usr/local/include/coin/OsiBranchingObject.hpp
-- Installing: /usr/local/include/coin/CoinPresolveZeros.hpp
-- Installing: /usr/local/include/coin/CbcConsequence.hpp
-- Installing: /usr/local/include/coin/ClpNode.hpp
-- Installing: /usr/local/include/coin/ClpSimplexDual.hpp
-- Installing: /usr/local/include/coin/ClpObjective.hpp
-- Installing: /usr/local/include/coin/ClpPEDualRowSteepest.hpp
-- Installing: /usr/local/include/coin/CbcMipStartIO.hpp
-- Installing: /usr/local/include/coin/CoinFloatEqual.hpp
-- Installing: /usr/local/include/coin/CoinSearchTree.hpp
-- Installing: /usr/local/include/coin/CglRedSplitParam.hpp
-- Installing: /usr/local/include/coin/CbcSolver.hpp
-- Installing: /usr/local/include/coin/OsiClpSolverInterface.hpp
-- Installing: /usr/local/include/coin/CbcBranchDefaultDecision.hpp
-- Installing: /usr/local/include/coin/ClpDualRowPivot.hpp
-- Installing: /usr/local/include/coin/CoinOslFactorization.hpp
-- Installing: /usr/local/include/coin/CbcStrategy.hpp
-- Installing: /usr/local/include/coin/CoinUtility.hpp
-- Installing: /usr/local/include/coin/CbcGeneral.hpp
-- Installing: /usr/local/include/coin/CoinWarmStartBasis.hpp
-- Installing: /usr/local/include/coin/ClpCholeskyBase.hpp
-- Installing: /usr/local/include/coin/ClpPEPrimalColumnSteepest.hpp
-- Installing: /usr/local/include/coin/CoinPresolveSubst.hpp
-- Installing: /usr/local/include/coin/CoinFileIO.hpp
-- Installing: /usr/local/include/coin/ClpSimplexNonlinear.hpp
-- Installing: /usr/local/include/coin/ClpMatrixBase.hpp
-- Installing: /usr/local/include/coin/CoinStructuredModel.hpp
-- Installing: /usr/local/include/coin/ClpEventHandler.hpp
-- Installing: /usr/local/include/coin/CoinShallowPackedVector.hpp
-- Installing: /usr/local/include/coin/ClpConstraintAmpl.hpp
-- Installing: /usr/local/include/coin/CbcCompare.hpp
-- Installing: /usr/local/include/coin/CglRedSplit.hpp
-- Installing: /usr/local/include/coin/CbcTreeLocal.hpp
-- Installing: /usr/local/include/coin/CglParam.hpp
-- Installing: /usr/local/include/coin/ClpGubMatrix.hpp
-- Installing: /usr/local/include/coin/CbcCutModifier.hpp
-- Installing: /usr/local/include/coin/OsiChooseVariable.hpp
-- Installing: /usr/local/include/coin/OsiRowCutDebugger.hpp
-- Installing: /usr/local/include/coin/CglLiftAndProject.hpp
-- Installing: /usr/local/include/coin/CoinFinite.hpp
-- Installing: /usr/local/include/coin/CbcHeuristicPivotAndFix.hpp
-- Installing: /usr/local/include/coin/CglDuplicateRow.hpp
-- Installing: /usr/local/include/coin/CoinWarmStartDual.hpp
-- Installing: /usr/local/include/coin/ClpNonLinearCost.hpp
-- Installing: /usr/local/include/coin/CglProbing.hpp
-- Installing: /usr/local/include/coin/CbcHeuristicVND.hpp
-- Installing: /usr/local/include/coin/ClpPESimplex.hpp
-- Installing: /usr/local/include/coin/CbcFollowOn.hpp
-- Installing: /usr/local/include/coin/ClpSolve.hpp
-- Installing: /usr/local/include/coin/CbcSimpleIntegerPseudoCost.hpp
-- Installing: /usr/local/include/coin/CbcHeuristicDiveCoefficient.hpp
-- Installing: /usr/local/include/coin/CbcSubProblem.hpp
-- Installing: /usr/local/include/coin/OsiConfig.h
-- Installing: /usr/local/include/coin/CbcCutSubsetModifier.hpp
-- Installing: /usr/local/include/coin/Clp_ampl.h
-- Installing: /usr/local/include/coin/OsiSolverInterface.hpp
-- Installing: /usr/local/include/coin/CbcCompareDepth.hpp
-- Installing: /usr/local/include/coin/CoinDenseVector.hpp
-- Installing: /usr/local/include/coin/CoinPresolveSingleton.hpp
-- Installing: /usr/local/include/coin/CoinWarmStartVector.hpp
-- Installing: /usr/local/include/coin/CbcSOS.hpp
-- Installing: /usr/local/include/coin/CbcSimpleInteger.hpp
-- Installing: /usr/local/include/coin/CbcNode.hpp
-- Installing: /usr/local/include/coin/CglGMIParam.hpp
-- Installing: /usr/local/include/coin/CoinPresolveEmpty.hpp
-- Installing: /usr/local/include/coin/CbcHeuristicDINS.hpp
-- Installing: /usr/local/include/coin/CbcEventHandler.hpp
-- Installing: /usr/local/include/coin/ClpFactorization.hpp
-- Installing: /usr/local/include/coin/CglKnapsackCover.hpp
-- Installing: /usr/local/include/coin/CoinSmartPtr.hpp
-- Installing: /usr/local/include/coin/CbcHeuristicGreedy.hpp
-- Installing: /usr/local/include/coin/ClpPackedMatrix.hpp
-- Installing: /usr/local/include/coin/MyEventHandler.hpp
-- Installing: /usr/local/include/coin/ClpSimplexPrimal.hpp
-- Installing: /usr/local/include/coin/CoinLpIO.hpp
-- Installing: /usr/local/include/coin/ClpGubDynamicMatrix.hpp
-- Installing: /usr/local/include/coin/CglResidualCapacity.hpp
-- Installing: /usr/local/include/coin/CbcBranchCut.hpp
-- Installing: /usr/local/include/coin/CglMixedIntegerRounding2.hpp
-- Installing: /usr/local/include/coin/CoinError.hpp
-- Installing: /usr/local/include/coin/CoinPresolveForcing.hpp
-- Installing: /usr/local/include/coin/CoinFactorization.hpp
-- Installing: /usr/local/include/coin/CbcMessage.hpp
-- Installing: /usr/local/include/coin/CoinPresolveDual.hpp
-- Installing: /usr/local/include/coin/CoinUtilsConfig.h
-- Installing: /usr/local/include/coin/CoinPresolveUseless.hpp
-- Installing: /usr/local/include/coin/OsiPresolve.hpp
-- Installing: /usr/local/include/coin/CbcBranchingObject.hpp
-- Installing: /usr/local/include/coin/OsiSolverParameters.hpp
-- Installing: /usr/local/include/coin/Cbc_C_Interface.h
-- Installing: /usr/local/include/coin/CoinIndexedVector.hpp
-- Installing: /usr/local/include/coin/ClpSimplex.hpp
-- Installing: /usr/local/include/coin/CbcHeuristicDW.hpp
-- Installing: /usr/local/include/coin/Cbc_ampl.h
-- Installing: /usr/local/include/coin/ClpSimplexOther.hpp
-- Installing: /usr/local/include/coin/CbcTree.hpp
-- Installing: /usr/local/include/coin/CglFlowCover.hpp
-- Installing: /usr/local/include/coin/CoinModelUseful.hpp
-- Installing: /usr/local/include/coin/CglOddHole.hpp
-- Installing: /usr/local/include/coin/CoinBuild.hpp
-- Installing: /usr/local/include/coin/CbcOrClpParam.cpp
-- Installing: /usr/local/include/coin/CoinTime.hpp
-- Installing: /usr/local/include/coin/CglRedSplit2.hpp
-- Installing: /usr/local/include/coin/ClpPEPrimalColumnDantzig.hpp
-- Installing: /usr/local/include/coin/CbcCompareEstimate.hpp
-- Installing: /usr/local/include/coin/CglGomory.hpp
-- Installing: /usr/local/include/coin/ClpLinearObjective.hpp
-- Installing: /usr/local/include/coin/CglConfig.h
-- Installing: /usr/local/include/coin/CbcBranchAllDifferent.hpp
-- Installing: /usr/local/include/coin/CbcHeuristicFPump.hpp
-- Installing: /usr/local/include/coin/CoinSimpFactorization.hpp
-- Installing: /usr/local/include/coin/config_coinutils.h
-- Installing: /usr/local/include/coin/CbcBranchDynamic.hpp
-- Installing: /usr/local/include/coin/ClpModel.hpp
-- Installing: /usr/local/include/coin/CbcFixVariable.hpp
-- Installing: /usr/local/include/coin/CoinTypes.hpp
-- Installing: /usr/local/include/coin/CglLandPTabRow.hpp
-- Installing: /usr/local/include/coin/CoinPragma.hpp
-- Installing: /usr/local/include/coin/CbcConfig.h
-- Installing: /usr/local/include/coin/CoinPresolveFixed.hpp
-- Installing: /usr/local/include/coin/CoinPresolvePsdebug.hpp
-- Installing: /usr/local/include/coin/CglCutGenerator.hpp
-- Installing: /usr/local/include/coin/CglGMI.hpp
-- Installing: /usr/local/include/coin/CbcHeuristicDive.hpp
-- Installing: /usr/local/include/coin/OsiColCut.hpp
-- Installing: /usr/local/include/coin/Cgl012cut.hpp
-- Installing: /usr/local/include/coin/CbcGeneralDepth.hpp
-- Installing: /usr/local/include/coin/CbcObjectUpdateData.hpp
-- Installing: /usr/local/include/coin/CoinWarmStart.hpp
-- Installing: /usr/local/include/coin/CbcHeuristic.hpp
-- Installing: /usr/local/include/coin/CbcFeasibilityBase.hpp
-- Installing: /usr/local/include/coin/config_cgl.h
-- Installing: /usr/local/include/coin/CbcSimpleIntegerDynamicPseudoCost.hpp
-- Installing: /usr/local/include/coin/CglTreeInfo.hpp
-- Installing: /usr/local/include/coin/CbcModel.hpp
-- Installing: /usr/local/include/coin/ClpAmplObjective.hpp
-- Installing: /usr/local/include/coin/CglSimpleRounding.hpp
-- Installing: /usr/local/include/coin/ClpQuadraticObjective.hpp
-- Installing: /usr/local/include/coin/CglAllDifferent.hpp
-- Installing: /usr/local/include/coin/CbcCountRowCut.hpp
-- Installing: /usr/local/include/coin/ClpDualRowSteepest.hpp
-- Installing: /usr/local/include/coin/CbcBranchActual.hpp
-- Installing: /usr/local/include/coin/CbcClique.hpp
-- Installing: /usr/local/include/coin/CbcLinked.hpp
-- Installing: /usr/local/include/coin/CbcHeuristicDiveLineSearch.hpp
-- Installing: /usr/local/include/coin/CbcHeuristicRENS.hpp
-- Installing: /usr/local/include/coin/CoinSort.hpp
-- Installing: /usr/local/include/coin/CoinPresolveMonitor.hpp
-- Installing: /usr/local/include/coin/CbcFathomDynamicProgramming.hpp
-- Installing: /usr/local/include/coin/CoinPresolveDoubleton.hpp
-- Installing: /usr/local/include/coin/CbcBranchDecision.hpp
-- Installing: /usr/local/include/coin/CbcCompareDefault.hpp
-- Installing: /usr/local/include/coin/CglStored.hpp
-- Installing: /usr/local/include/coin/CbcParam.hpp
-- Installing: /usr/local/include/coin/ClpPrimalColumnSteepest.hpp
-- Installing: /usr/local/include/coin/OsiCollections.hpp
-- Installing: /usr/local/include/coin/ClpDynamicExampleMatrix.hpp
-- Installing: /usr/local/include/coin/CbcOrClpParam.hpp
-- Installing: /usr/local/include/coin/OsiSolverBranch.hpp
-- Installing: /usr/local/include/coin/ClpPresolve.hpp
-- Installing: /usr/local/include/coin/ClpMessage.hpp
-- Installing: /usr/local/include/coin/ClpPlusMinusOneMatrix.hpp
-- Installing: /usr/local/include/coin/CglLandP.hpp
-- Installing: /usr/local/include/coin/CoinPackedVectorBase.hpp
-- Installing: /usr/local/include/coin/OsiCut.hpp
-- Installing: /usr/local/include/coin/CbcFathom.hpp
-- Installing: /usr/local/include/coin/config_osi.h
-- Installing: /usr/local/include/coin/Coin_C_defines.h
-- Installing: /usr/local/include/coin/CoinPresolveDupcol.hpp
-- Installing: /usr/local/include/coin/CglLandPMessages.hpp
-- Installing: /usr/local/include/coin/CoinSignal.hpp
-- Installing: /usr/local/include/coin/CoinPresolveTripleton.hpp
-- Installing: /usr/local/include/coin/CglLandPSimplex.hpp
-- Installing: /usr/local/include/coin/CoinMpsIO.hpp
-- Installing: /usr/local/include/coin/CbcFullNodeInfo.hpp
-- Installing: /usr/local/include/coin/CbcNodeInfo.hpp
-- Installing: /usr/local/include/coin/CbcBranchBase.hpp
-- Installing: /usr/local/include/coin/CoinRational.hpp
-- Installing: /usr/local/include/coin/CoinSnapshot.hpp
-- Installing: /usr/local/include/coin/CbcHeuristicDiveGuided.hpp
-- Installing: /usr/local/include/coin/CbcPartialNodeInfo.hpp
-- Installing: /usr/local/include/coin/ClpDualRowDantzig.hpp
-- Installing: /usr/local/include/coin/CoinPackedMatrix.hpp
-- Installing: /usr/local/include/coin/ClpDummyMatrix.hpp
-- Installing: /usr/local/include/coin/ClpConstraintQuadratic.hpp
-- Installing: /usr/local/include/coin/CbcDummyBranchingObject.hpp
-- Installing: /usr/local/include/coin/Idiot.hpp
-- Installing: /usr/local/include/coin/config_clp.h
-- Installing: /usr/local/include/coin/CoinModel.hpp
-- Installing: /usr/local/include/coin/ClpPEDualRowDantzig.hpp
-- Installing: /usr/local/include/coin/ClpConfig.h
-- Installing: /usr/local/include/coin/CoinMessage.hpp
-- Installing: /usr/local/include/coin/CbcHeuristicDiveVectorLength.hpp
-- Installing: /usr/local/include/coin/CglLandPValidator.hpp
-- Installing: /usr/local/include/coin/ClpConstraintLinear.hpp
-- Installing: /usr/local/include/coin/CoinPresolveImpliedFree.hpp
-- Installing: /usr/local/include/coin/CoinDistance.hpp
-- Installing: /usr/local/include/coin/CoinWarmStartPrimalDual.hpp
-- Installing: /usr/local/include/coin/CglRedSplit2Param.hpp
-- Installing: /usr/local/include/coin/OsiAuxInfo.hpp
-- Installing: /usr/local/include/coin/ClpPrimalColumnDantzig.hpp
-- Installing: /usr/local/include/coin/CglLandPUtils.hpp
-- Installing: /usr/local/include/coin/CoinPresolveIsolated.hpp
-- Installing: /usr/local/include/coin/ClpNetworkMatrix.hpp
-- Installing: /usr/local/include/coin/ClpConstraint.hpp
-- Installing: /usr/local/include/coin/CbcNWay.hpp
-- Installing: /usr/local/include/coin/CglTwomir.hpp
-- Installing: /usr/local/include/coin/CbcHeuristicRandRound.hpp
-- Installing: /usr/local/include/coin/config_cbc.h
-- Installing: /usr/local/include/coin/CoinDenseFactorization.hpp
-- Installing: /usr/local/include/coin/OsiCbcSolverInterface.hpp
-- Installing: /usr/local/include/coin/OsiRowCut.hpp
-- Installing: /usr/local/include/coin/CoinPackedVector.hpp
-- Installing: /usr/local/include/coin/OsiCuts.hpp
-- Installing: /usr/local/include/coin/CglMixedIntegerRounding.hpp
-- Installing: /usr/local/include/coin/CbcHeuristicRINS.hpp
-- Installing: /usr/local/include/coin/CbcHeuristicDivePseudoCost.hpp
-- Installing: /usr/local/include/coin/ClpPdcoBase.hpp
-- Installing: /usr/local/include/coin/CoinAlloc.hpp
-- Installing: /usr/local/include/coin/CoinPresolveTighten.hpp
-- Installing: /usr/local/include/coin/CoinPresolveMatrix.hpp
-- Installing: /usr/local/include/coin/CoinMessageHandler.hpp
-- Installing: /usr/local/include/coin/ClpDynamicMatrix.hpp
-- Installing: /usr/local/include/coin/CbcBranchToFixLots.hpp
-- Installing: /usr/local/include/coin/unitTest.cpp
-- Installing: /usr/local/include/coin/CbcCompareObjective.hpp
-- Installing: /usr/local/include/coin/Clp_C_Interface.h
-- Installing: /usr/local/include/coin/CbcCutGenerator.hpp
-- Installing: /usr/local/include/coin/CoinHelperFunctions.hpp
-- Installing: /usr/local/include/coin/ClpPdco.hpp
-- Installing: /usr/local/include/lpi
-- Installing: /usr/local/include/lpi/lpi.h
-- Installing: /usr/local/include/lpi/type_lpi.h
-- Installing: /usr/local/include/re2
-- Installing: /usr/local/include/re2/re2.h
-- Installing: /usr/local/include/re2/set.h
-- Installing: /usr/local/include/re2/filtered_re2.h
-- Installing: /usr/local/include/re2/stringpiece.h
-- Installing: /usr/local/include/ortools
-- Installing: /usr/local/include/ortools/scheduling
-- Installing: /usr/local/include/ortools/scheduling/rcpsp_parser.h
-- Installing: /usr/local/include/ortools/scheduling/jobshop_scheduling_parser.h
-- Installing: /usr/local/include/ortools/scheduling/rcpsp.pb.h
-- Installing: /usr/local/include/ortools/scheduling/testdata
-- Installing: /usr/local/include/ortools/scheduling/python
-- Installing: /usr/local/include/ortools/scheduling/course_scheduling.pb.h
-- Installing: /usr/local/include/ortools/scheduling/jobshop_scheduling.pb.h
-- Installing: /usr/local/include/ortools/math_opt
-- Installing: /usr/local/include/ortools/math_opt/model.pb.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/base_solver_test.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/ip_model_solve_parameters_tests.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/test_models.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/lp_model_solve_parameters_tests.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/second_order_cone_tests.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/lp_parameter_tests.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/lp_initial_basis_tests.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/qc_tests.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/logical_constraint_tests.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/ip_multiple_solutions_tests.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/testdata
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/infeasible_subsystem_tests.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/qp_tests.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/status_tests.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/generic_tests.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/multi_objective_tests.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/mip_tests.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/invalid_input_tests.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/lp_tests.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/ip_parameter_tests.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/lp_incomplete_solve_tests.h
-- Installing: /usr/local/include/ortools/math_opt/solver_tests/callback_tests.h
-- Installing: /usr/local/include/ortools/math_opt/tools
-- Installing: /usr/local/include/ortools/math_opt/tools/file_format_flags.h
-- Installing: /usr/local/include/ortools/math_opt/model_parameters.pb.h
-- Installing: /usr/local/include/ortools/math_opt/samples
-- Installing: /usr/local/include/ortools/math_opt/samples/python
-- Installing: /usr/local/include/ortools/math_opt/samples/cpp
-- Installing: /usr/local/include/ortools/math_opt/core
-- Installing: /usr/local/include/ortools/math_opt/core/concurrent_calls_guard.h
-- Installing: /usr/local/include/ortools/math_opt/core/c_api
-- Installing: /usr/local/include/ortools/math_opt/core/c_api/solver.h
-- Installing: /usr/local/include/ortools/math_opt/core/invalid_indicators.h
-- Installing: /usr/local/include/ortools/math_opt/core/inverted_bounds.h
-- Installing: /usr/local/include/ortools/math_opt/core/non_streamable_solver_init_arguments.h
-- Installing: /usr/local/include/ortools/math_opt/core/solve_interrupter.h
-- Installing: /usr/local/include/ortools/math_opt/core/math_opt_proto_utils.h
-- Installing: /usr/local/include/ortools/math_opt/core/empty_bounds.h
-- Installing: /usr/local/include/ortools/math_opt/core/sparse_submatrix.h
-- Installing: /usr/local/include/ortools/math_opt/core/sorted.h
-- Installing: /usr/local/include/ortools/math_opt/core/python
-- Installing: /usr/local/include/ortools/math_opt/core/solver_debug.h
-- Installing: /usr/local/include/ortools/math_opt/core/sparse_vector.h
-- Installing: /usr/local/include/ortools/math_opt/core/solver_interface.h
-- Installing: /usr/local/include/ortools/math_opt/core/model_summary.h
-- Installing: /usr/local/include/ortools/math_opt/core/solver.h
-- Installing: /usr/local/include/ortools/math_opt/core/arrow_operator_proxy.h
-- Installing: /usr/local/include/ortools/math_opt/core/sparse_vector_view.h
-- Installing: /usr/local/include/ortools/math_opt/constraints
-- Installing: /usr/local/include/ortools/math_opt/constraints/quadratic
-- Installing: /usr/local/include/ortools/math_opt/constraints/quadratic/quadratic_constraint.h
-- Installing: /usr/local/include/ortools/math_opt/constraints/quadratic/storage.h
-- Installing: /usr/local/include/ortools/math_opt/constraints/quadratic/validator.h
-- Installing: /usr/local/include/ortools/math_opt/constraints/indicator
-- Installing: /usr/local/include/ortools/math_opt/constraints/indicator/indicator_constraint.h
-- Installing: /usr/local/include/ortools/math_opt/constraints/indicator/storage.h
-- Installing: /usr/local/include/ortools/math_opt/constraints/indicator/validator.h
-- Installing: /usr/local/include/ortools/math_opt/constraints/util
-- Installing: /usr/local/include/ortools/math_opt/constraints/util/model_util.h
-- Installing: /usr/local/include/ortools/math_opt/constraints/second_order_cone
-- Installing: /usr/local/include/ortools/math_opt/constraints/second_order_cone/storage.h
-- Installing: /usr/local/include/ortools/math_opt/constraints/second_order_cone/validator.h
-- Installing: /usr/local/include/ortools/math_opt/constraints/second_order_cone/second_order_cone_constraint.h
-- Installing: /usr/local/include/ortools/math_opt/constraints/sos
-- Installing: /usr/local/include/ortools/math_opt/constraints/sos/sos2_constraint.h
-- Installing: /usr/local/include/ortools/math_opt/constraints/sos/util.h
-- Installing: /usr/local/include/ortools/math_opt/constraints/sos/storage.h
-- Installing: /usr/local/include/ortools/math_opt/constraints/sos/sos1_constraint.h
-- Installing: /usr/local/include/ortools/math_opt/constraints/sos/validator.h
-- Installing: /usr/local/include/ortools/math_opt/result.pb.h
-- Installing: /usr/local/include/ortools/math_opt/storage
-- Installing: /usr/local/include/ortools/math_opt/storage/range.h
-- Installing: /usr/local/include/ortools/math_opt/storage/atomic_constraint_storage.h
-- Installing: /usr/local/include/ortools/math_opt/storage/sparse_coefficient_map.h
-- Installing: /usr/local/include/ortools/math_opt/storage/update_trackers.h
-- Installing: /usr/local/include/ortools/math_opt/storage/linear_constraint_storage.h
-- Installing: /usr/local/include/ortools/math_opt/storage/model_storage.h
-- Installing: /usr/local/include/ortools/math_opt/storage/linear_expression_data.h
-- Installing: /usr/local/include/ortools/math_opt/storage/sparse_matrix.h
-- Installing: /usr/local/include/ortools/math_opt/storage/model_storage_types.h
-- Installing: /usr/local/include/ortools/math_opt/storage/iterators.h
-- Installing: /usr/local/include/ortools/math_opt/storage/objective_storage.h
-- Installing: /usr/local/include/ortools/math_opt/storage/variable_storage.h
-- Installing: /usr/local/include/ortools/math_opt/callback.pb.h
-- Installing: /usr/local/include/ortools/math_opt/model_update.pb.h
-- Installing: /usr/local/include/ortools/math_opt/infeasible_subsystem.pb.h
-- Installing: /usr/local/include/ortools/math_opt/validators
-- Installing: /usr/local/include/ortools/math_opt/validators/infeasible_subsystem_validator.h
-- Installing: /usr/local/include/ortools/math_opt/validators/linear_expression_validator.h
-- Installing: /usr/local/include/ortools/math_opt/validators/result_validator.h
-- Installing: /usr/local/include/ortools/math_opt/validators/sparse_vector_validator.h
-- Installing: /usr/local/include/ortools/math_opt/validators/solution_validator.h
-- Installing: /usr/local/include/ortools/math_opt/validators/solve_stats_validator.h
-- Installing: /usr/local/include/ortools/math_opt/validators/termination_validator.h
-- Installing: /usr/local/include/ortools/math_opt/validators/callback_validator.h
-- Installing: /usr/local/include/ortools/math_opt/validators/scalar_validator.h
-- Installing: /usr/local/include/ortools/math_opt/validators/model_parameters_validator.h
-- Installing: /usr/local/include/ortools/math_opt/validators/bounds_and_status_validator.h
-- Installing: /usr/local/include/ortools/math_opt/validators/model_validator.h
-- Installing: /usr/local/include/ortools/math_opt/validators/ids_validator.h
-- Installing: /usr/local/include/ortools/math_opt/validators/solve_parameters_validator.h
-- Installing: /usr/local/include/ortools/math_opt/validators/sparse_matrix_validator.h
-- Installing: /usr/local/include/ortools/math_opt/python
-- Installing: /usr/local/include/ortools/math_opt/python/testing
-- Installing: /usr/local/include/ortools/math_opt/python/ipc
-- Installing: /usr/local/include/ortools/math_opt/testing
-- Installing: /usr/local/include/ortools/math_opt/testing/param_name.h
-- Installing: /usr/local/include/ortools/math_opt/testing/stream.h
-- Installing: /usr/local/include/ortools/math_opt/solvers
-- Installing: /usr/local/include/ortools/math_opt/solvers/highs.pb.h
-- Installing: /usr/local/include/ortools/math_opt/solvers/glpk.pb.h
-- Installing: /usr/local/include/ortools/math_opt/solvers/gurobi.pb.h
-- Installing: /usr/local/include/ortools/math_opt/solvers/gscip_solver.h
-- Installing: /usr/local/include/ortools/math_opt/solvers/gurobi_init_arguments.h
-- Installing: /usr/local/include/ortools/math_opt/solvers/gscip
-- Installing: /usr/local/include/ortools/math_opt/solvers/gscip/gscip_solver_constraint_handler.h
-- Installing: /usr/local/include/ortools/math_opt/solvers/message_callback_data.h
-- Installing: /usr/local/include/ortools/math_opt/solvers/gurobi_solver.h
-- Installing: /usr/local/include/ortools/math_opt/solvers/gurobi_callback.h
-- Installing: /usr/local/include/ortools/math_opt/solvers/pdlp_solver.h
-- Installing: /usr/local/include/ortools/math_opt/solvers/osqp.pb.h
-- Installing: /usr/local/include/ortools/math_opt/solvers/glop_solver.h
-- Installing: /usr/local/include/ortools/math_opt/solvers/glpk
-- Installing: /usr/local/include/ortools/math_opt/solvers/glpk/rays.h
-- Installing: /usr/local/include/ortools/math_opt/solvers/glpk/gap.h
-- Installing: /usr/local/include/ortools/math_opt/solvers/glpk/glpk_sparse_vector.h
-- Installing: /usr/local/include/ortools/math_opt/solvers/cp_sat_solver.h
-- Installing: /usr/local/include/ortools/math_opt/solvers/pdlp_bridge.h
-- Installing: /usr/local/include/ortools/math_opt/solvers/gurobi
-- Installing: /usr/local/include/ortools/math_opt/solvers/gurobi/g_gurobi.h
-- Installing: /usr/local/include/ortools/math_opt/solvers/glpk_solver.h
-- Installing: /usr/local/include/ortools/math_opt/sparse_containers.pb.h
-- Installing: /usr/local/include/ortools/math_opt/rpc.pb.h
-- Installing: /usr/local/include/ortools/math_opt/solution.pb.h
-- Installing: /usr/local/include/ortools/math_opt/io
-- Installing: /usr/local/include/ortools/math_opt/io/lp_converter.h
-- Installing: /usr/local/include/ortools/math_opt/io/mps_converter.h
-- Installing: /usr/local/include/ortools/math_opt/io/names_removal.h
-- Installing: /usr/local/include/ortools/math_opt/io/proto_converter.h
-- Installing: /usr/local/include/ortools/math_opt/labs
-- Installing: /usr/local/include/ortools/math_opt/labs/solution_feasibility_checker.h
-- Installing: /usr/local/include/ortools/math_opt/labs/solution_improvement.h
-- Installing: /usr/local/include/ortools/math_opt/labs/linear_expr_util.h
-- Installing: /usr/local/include/ortools/math_opt/labs/general_constraint_to_mip.h
-- Installing: /usr/local/include/ortools/math_opt/parameters.pb.h
-- Installing: /usr/local/include/ortools/math_opt/cpp
-- Installing: /usr/local/include/ortools/math_opt/cpp/objective.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/parameters.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/solver_init_arguments.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/solve_arguments.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/update_tracker.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/compute_infeasible_subsystem_result.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/basis_status.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/solve.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/update_result.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/model.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/compute_infeasible_subsystem_arguments.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/variable_and_expressions.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/solve_result.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/linear_constraint.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/matchers.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/map_filter.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/statistics.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/solution.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/model_solve_parameters.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/message_callback.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/streamable_solver_init_arguments.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/key_types.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/math_opt.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/enums.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/formatters.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/solver_resources.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/sparse_containers.h
-- Installing: /usr/local/include/ortools/math_opt/cpp/callback.h
-- Installing: /usr/local/include/ortools/gscip
-- Installing: /usr/local/include/ortools/gscip/gscip.h
-- Installing: /usr/local/include/ortools/gscip/gscip_parameters.h
-- Installing: /usr/local/include/ortools/gscip/gscip.pb.h
-- Installing: /usr/local/include/ortools/gscip/gscip_event_handler.h
-- Installing: /usr/local/include/ortools/gscip/gscip_callback_result.h
-- Installing: /usr/local/include/ortools/gscip/legacy_scip_params.h
-- Installing: /usr/local/include/ortools/gscip/gscip_message_handler.h
-- Installing: /usr/local/include/ortools/gscip/gscip_ext.h
-- Installing: /usr/local/include/ortools/gscip/gscip_constraint_handler.h
-- Installing: /usr/local/include/ortools/bop
-- Installing: /usr/local/include/ortools/bop/bop_ls.h
-- Installing: /usr/local/include/ortools/bop/integral_solver.h
-- Installing: /usr/local/include/ortools/bop/bop_util.h
-- Installing: /usr/local/include/ortools/bop/bop_lns.h
-- Installing: /usr/local/include/ortools/bop/bop_types.h
-- Installing: /usr/local/include/ortools/bop/bop_fs.h
-- Installing: /usr/local/include/ortools/bop/bop_solver.h
-- Installing: /usr/local/include/ortools/bop/bop_parameters.pb.h
-- Installing: /usr/local/include/ortools/bop/bop_solution.h
-- Installing: /usr/local/include/ortools/bop/bop_portfolio.h
-- Installing: /usr/local/include/ortools/bop/bop_base.h
-- Installing: /usr/local/include/ortools/bop/complete_optimizer.h
-- Installing: /usr/local/include/ortools/linear_solver
-- Installing: /usr/local/include/ortools/linear_solver/glop_utils.h
-- Installing: /usr/local/include/ortools/linear_solver/linear_expr.h
-- Installing: /usr/local/include/ortools/linear_solver/proto_solver
-- Installing: /usr/local/include/ortools/linear_solver/proto_solver/gurobi_proto_solver.h
-- Installing: /usr/local/include/ortools/linear_solver/proto_solver/scip_proto_solver.h
-- Installing: /usr/local/include/ortools/linear_solver/proto_solver/sat_proto_solver.h
-- Installing: /usr/local/include/ortools/linear_solver/proto_solver/xpress_proto_solver.h
-- Installing: /usr/local/include/ortools/linear_solver/proto_solver/pdlp_proto_solver.h
-- Installing: /usr/local/include/ortools/linear_solver/proto_solver/glop_proto_solver.h
-- Installing: /usr/local/include/ortools/linear_solver/proto_solver/proto_utils.h
-- Installing: /usr/local/include/ortools/linear_solver/proto_solver/highs_proto_solver.h
-- Installing: /usr/local/include/ortools/linear_solver/proto_solver/sat_solver_utils.h
-- Installing: /usr/local/include/ortools/linear_solver/model_exporter.h
-- Installing: /usr/local/include/ortools/linear_solver/samples
-- Installing: /usr/local/include/ortools/linear_solver/model_exporter_swig_helper.h
-- Installing: /usr/local/include/ortools/linear_solver/linear_solver.h
-- Installing: /usr/local/include/ortools/linear_solver/scip_helper_macros.h
-- Installing: /usr/local/include/ortools/linear_solver/linear_solver.pb.h
-- Installing: /usr/local/include/ortools/linear_solver/csharp
-- Installing: /usr/local/include/ortools/linear_solver/testdata
-- Installing: /usr/local/include/ortools/linear_solver/python
-- Installing: /usr/local/include/ortools/linear_solver/linear_solver_callback.h
-- Installing: /usr/local/include/ortools/linear_solver/scip_callback.h
-- Installing: /usr/local/include/ortools/linear_solver/model_validator.h
-- Installing: /usr/local/include/ortools/linear_solver/solve_mp_model.h
-- Installing: /usr/local/include/ortools/linear_solver/java
-- Installing: /usr/local/include/ortools/linear_solver/wrappers
-- Installing: /usr/local/include/ortools/linear_solver/wrappers/model_builder_helper.h
-- Installing: /usr/local/include/ortools/glop
-- Installing: /usr/local/include/ortools/glop/preprocessor.h
-- Installing: /usr/local/include/ortools/glop/revised_simplex.h
-- Installing: /usr/local/include/ortools/glop/samples
-- Installing: /usr/local/include/ortools/glop/variable_values.h
-- Installing: /usr/local/include/ortools/glop/lp_solver.h
-- Installing: /usr/local/include/ortools/glop/primal_edge_norms.h
-- Installing: /usr/local/include/ortools/glop/lu_factorization.h
-- Installing: /usr/local/include/ortools/glop/status.h
-- Installing: /usr/local/include/ortools/glop/initial_basis.h
-- Installing: /usr/local/include/ortools/glop/dual_edge_norms.h
-- Installing: /usr/local/include/ortools/glop/entering_variable.h
-- Installing: /usr/local/include/ortools/glop/rank_one_update.h
-- Installing: /usr/local/include/ortools/glop/pricing.h
-- Installing: /usr/local/include/ortools/glop/parameters_validation.h
-- Installing: /usr/local/include/ortools/glop/update_row.h
-- Installing: /usr/local/include/ortools/glop/markowitz.h
-- Installing: /usr/local/include/ortools/glop/reduced_costs.h
-- Installing: /usr/local/include/ortools/glop/parameters.pb.h
-- Installing: /usr/local/include/ortools/glop/basis_representation.h
-- Installing: /usr/local/include/ortools/glop/variables_info.h
-- Installing: /usr/local/include/ortools/packing
-- Installing: /usr/local/include/ortools/packing/arc_flow_solver.h
-- Installing: /usr/local/include/ortools/packing/binpacking_2d_parser.h
-- Installing: /usr/local/include/ortools/packing/vector_bin_packing.pb.h
-- Installing: /usr/local/include/ortools/packing/arc_flow_builder.h
-- Installing: /usr/local/include/ortools/packing/testdata
-- Installing: /usr/local/include/ortools/packing/multiple_dimensions_bin_packing.pb.h
-- Installing: /usr/local/include/ortools/packing/vector_bin_packing_parser.h
-- Installing: /usr/local/include/ortools/service
-- Installing: /usr/local/include/ortools/service/v1
-- Installing: /usr/local/include/ortools/service/v1/mathopt
-- Installing: /usr/local/include/ortools/flatzinc
-- Installing: /usr/local/include/ortools/flatzinc/mznlib
-- Installing: /usr/local/include/ortools/flatzinc/presolve.h
-- Installing: /usr/local/include/ortools/flatzinc/cp_model_fz_solver.h
-- Installing: /usr/local/include/ortools/flatzinc/parser.h
-- Installing: /usr/local/include/ortools/flatzinc/model.h
-- Installing: /usr/local/include/ortools/flatzinc/checker.h
-- Installing: /usr/local/include/ortools/flatzinc/parser_util.h
-- Installing: /usr/local/include/ortools/julia
-- Installing: /usr/local/include/ortools/julia/docs
-- Installing: /usr/local/include/ortools/julia/ORToolsGenerated.jl
-- Installing: /usr/local/include/ortools/julia/ORToolsGenerated.jl/src
-- Installing: /usr/local/include/ortools/julia/ORToolsGenerated.jl/src/genproto
-- Installing: /usr/local/include/ortools/julia/ORToolsGenerated.jl/src/genproto/operations_research
-- Installing: /usr/local/include/ortools/julia/ORToolsGenerated.jl/src/genproto/operations_research/scheduling
-- Installing: /usr/local/include/ortools/julia/ORToolsGenerated.jl/src/genproto/operations_research/scheduling/jssp
-- Installing: /usr/local/include/ortools/julia/ORToolsGenerated.jl/src/genproto/operations_research/scheduling/rcpsp
-- Installing: /usr/local/include/ortools/julia/ORToolsGenerated.jl/src/genproto/operations_research/math_opt
-- Installing: /usr/local/include/ortools/julia/ORToolsGenerated.jl/src/genproto/operations_research/bop
-- Installing: /usr/local/include/ortools/julia/ORToolsGenerated.jl/src/genproto/operations_research/glop
-- Installing: /usr/local/include/ortools/julia/ORToolsGenerated.jl/src/genproto/operations_research/packing
-- Installing: /usr/local/include/ortools/julia/ORToolsGenerated.jl/src/genproto/operations_research/packing/vbp
-- Installing: /usr/local/include/ortools/julia/ORToolsGenerated.jl/src/genproto/operations_research/sat
-- Installing: /usr/local/include/ortools/julia/ORToolsGenerated.jl/src/genproto/operations_research/pdlp
-- Installing: /usr/local/include/ortools/julia/ORToolsGenerated.jl/src/genproto/google
-- Installing: /usr/local/include/ortools/julia/ORToolsGenerated.jl/src/genproto/google/protobuf
-- Installing: /usr/local/include/ortools/julia/ORToolsGenerated.jl/scripts
-- Installing: /usr/local/include/ortools/python
-- Installing: /usr/local/include/ortools/python/docs
-- Installing: /usr/local/include/ortools/util
-- Installing: /usr/local/include/ortools/util/fp_roundtrip_conv.h
-- Installing: /usr/local/include/ortools/util/optional_boolean.pb.h
-- Installing: /usr/local/include/ortools/util/affine_relation.h
-- Installing: /usr/local/include/ortools/util/sorted_interval_list.h
-- Installing: /usr/local/include/ortools/util/rev.h
-- Installing: /usr/local/include/ortools/util/running_stat.h
-- Installing: /usr/local/include/ortools/util/string_util.h
-- Installing: /usr/local/include/ortools/util/saturated_arithmetic.h
-- Installing: /usr/local/include/ortools/util/range_minimum_query.h
-- Installing: /usr/local/include/ortools/util/strong_integers.h
-- Installing: /usr/local/include/ortools/util/aligned_memory.h
-- Installing: /usr/local/include/ortools/util/stats.h
-- Installing: /usr/local/include/ortools/util/monoid_operation_tree.h
-- Installing: /usr/local/include/ortools/util/range_query_function.h
-- Installing: /usr/local/include/ortools/util/vector_sum.h
-- Installing: /usr/local/include/ortools/util/parse_proto.h
-- Installing: /usr/local/include/ortools/util/piecewise_linear_function.h
-- Installing: /usr/local/include/ortools/util/lazy_mutable_copy.h
-- Installing: /usr/local/include/ortools/util/sigint.h
-- Installing: /usr/local/include/ortools/util/bitset.h
-- Installing: /usr/local/include/ortools/util/testing_utils.h
-- Installing: /usr/local/include/ortools/util/zvector.h
-- Installing: /usr/local/include/ortools/util/functions_swig_helpers.h
-- Installing: /usr/local/include/ortools/util/adaptative_parameter_value.h
-- Installing: /usr/local/include/ortools/util/file_util.h
-- Installing: /usr/local/include/ortools/util/cached_log.h
-- Installing: /usr/local/include/ortools/util/vector_sum_internal.h
-- Installing: /usr/local/include/ortools/util/vector_or_function.h
-- Installing: /usr/local/include/ortools/util/int128.pb.h
-- Installing: /usr/local/include/ortools/util/rational_approximation.h
-- Installing: /usr/local/include/ortools/util/fp_roundtrip_conv_testing.h
-- Installing: /usr/local/include/ortools/util/time_limit.h
-- Installing: /usr/local/include/ortools/util/return_macros.h
-- Installing: /usr/local/include/ortools/util/csharp
-- Installing: /usr/local/include/ortools/util/status_macros.h
-- Installing: /usr/local/include/ortools/util/python
-- Installing: /usr/local/include/ortools/util/python/sorted_interval_list_doc.h
-- Installing: /usr/local/include/ortools/util/integer_pq.h
-- Installing: /usr/local/include/ortools/util/random_engine.h
-- Installing: /usr/local/include/ortools/util/logging.h
-- Installing: /usr/local/include/ortools/util/filelineiter.h
-- Installing: /usr/local/include/ortools/util/string_array.h
-- Installing: /usr/local/include/ortools/util/sort.h
-- Installing: /usr/local/include/ortools/util/proto_tools.h
-- Installing: /usr/local/include/ortools/util/permutation.h
-- Installing: /usr/local/include/ortools/util/java
-- Installing: /usr/local/include/ortools/util/tuple_set.h
-- Installing: /usr/local/include/ortools/util/functions_swig_test_helpers.h
-- Installing: /usr/local/include/ortools/util/aligned_memory_internal.h
-- Installing: /usr/local/include/ortools/util/fp_utils.h
-- Installing: /usr/local/include/ortools/util/flat_matrix.h
-- Installing: /usr/local/include/ortools/util/qap_reader.h
-- Installing: /usr/local/include/ortools/graph
-- Installing: /usr/local/include/ortools/graph/ebert_graph.h
-- Installing: /usr/local/include/ortools/graph/topologicalsorter.h
-- Installing: /usr/local/include/ortools/graph/connected_components.h
-- Installing: /usr/local/include/ortools/graph/strongly_connected_components.h
-- Installing: /usr/local/include/ortools/graph/christofides.h
-- Installing: /usr/local/include/ortools/graph/graph.h
-- Installing: /usr/local/include/ortools/graph/samples
-- Installing: /usr/local/include/ortools/graph/min_cost_flow.h
-- Installing: /usr/local/include/ortools/graph/util.h
-- Installing: /usr/local/include/ortools/graph/max_flow.h
-- Installing: /usr/local/include/ortools/graph/io.h
-- Installing: /usr/local/include/ortools/graph/assignment.h
-- Installing: /usr/local/include/ortools/graph/perfect_matching.h
-- Installing: /usr/local/include/ortools/graph/one_tree_lower_bound.h
-- Installing: /usr/local/include/ortools/graph/hamiltonian_path.h
-- Installing: /usr/local/include/ortools/graph/multi_dijkstra.h
-- Installing: /usr/local/include/ortools/graph/bfs.h
-- Installing: /usr/local/include/ortools/graph/csharp
-- Installing: /usr/local/include/ortools/graph/bidirectional_dijkstra.h
-- Installing: /usr/local/include/ortools/graph/testdata
-- Installing: /usr/local/include/ortools/graph/python
-- Installing: /usr/local/include/ortools/graph/dag_shortest_path.h
-- Installing: /usr/local/include/ortools/graph/minimum_spanning_tree.h
-- Installing: /usr/local/include/ortools/graph/iterators.h
-- Installing: /usr/local/include/ortools/graph/shortest_paths.h
-- Installing: /usr/local/include/ortools/graph/java
-- Installing: /usr/local/include/ortools/graph/linear_assignment.h
-- Installing: /usr/local/include/ortools/graph/graphs.h
-- Installing: /usr/local/include/ortools/graph/eulerian_path.h
-- Installing: /usr/local/include/ortools/graph/dag_constrained_shortest_path.h
-- Installing: /usr/local/include/ortools/graph/bounded_dijkstra.h
-- Installing: /usr/local/include/ortools/graph/cliques.h
-- Installing: /usr/local/include/ortools/graph/flow_problem.pb.h
-- Installing: /usr/local/include/ortools/routing
-- Installing: /usr/local/include/ortools/routing/nearp_parser.h
-- Installing: /usr/local/include/ortools/routing/samples
-- Installing: /usr/local/include/ortools/routing/simple_graph.h
-- Installing: /usr/local/include/ortools/routing/cvrptw_lib.h
-- Installing: /usr/local/include/ortools/routing/tsptw_parser.h
-- Installing: /usr/local/include/ortools/routing/testdata
-- Installing: /usr/local/include/ortools/routing/tsplib_parser.h
-- Installing: /usr/local/include/ortools/routing/solomon_parser.h
-- Installing: /usr/local/include/ortools/routing/carp_parser.h
-- Installing: /usr/local/include/ortools/routing/lilim_parser.h
-- Installing: /usr/local/include/ortools/routing/pdtsp_parser.h
-- Installing: /usr/local/include/ortools/routing/solution_serializer.h
-- Installing: /usr/local/include/ortools/init
-- Installing: /usr/local/include/ortools/init/init.h
-- Installing: /usr/local/include/ortools/init/csharp
-- Installing: /usr/local/include/ortools/init/python
-- Installing: /usr/local/include/ortools/init/python/init_doc.h
-- Installing: /usr/local/include/ortools/init/java
-- Installing: /usr/local/include/ortools/dotnet
-- Installing: /usr/local/include/ortools/dotnet/docs
-- Installing: /usr/local/include/ortools/dotnet/CreateSigningKey
-- Installing: /usr/local/include/ortools/sat
-- Installing: /usr/local/include/ortools/sat/pseudo_costs.h
-- Installing: /usr/local/include/ortools/sat/cp_model.pb.h
-- Installing: /usr/local/include/ortools/sat/timetable_edgefinding.h
-- Installing: /usr/local/include/ortools/sat/rins.h
-- Installing: /usr/local/include/ortools/sat/theta_tree.h
-- Installing: /usr/local/include/ortools/sat/cp_model.h
-- Installing: /usr/local/include/ortools/sat/feasibility_pump.h
-- Installing: /usr/local/include/ortools/sat/timetable.h
-- Installing: /usr/local/include/ortools/sat/cp_model_service.pb.h
-- Installing: /usr/local/include/ortools/sat/diophantine.h
-- Installing: /usr/local/include/ortools/sat/2d_orthogonal_packing_testing.h
-- Installing: /usr/local/include/ortools/sat/opb_reader.h
-- Installing: /usr/local/include/ortools/sat/samples
-- Installing: /usr/local/include/ortools/sat/table.h
-- Installing: /usr/local/include/ortools/sat/util.h
-- Installing: /usr/local/include/ortools/sat/routing_cuts.h
-- Installing: /usr/local/include/ortools/sat/feasibility_jump.h
-- Installing: /usr/local/include/ortools/sat/pb_constraint.h
-- Installing: /usr/local/include/ortools/sat/symmetry_util.h
-- Installing: /usr/local/include/ortools/sat/cp_model_presolve.h
-- Installing: /usr/local/include/ortools/sat/boolean_problem.pb.h
-- Installing: /usr/local/include/ortools/sat/cp_model_postsolve.h
-- Installing: /usr/local/include/ortools/sat/restart.h
-- Installing: /usr/local/include/ortools/sat/docs
-- Installing: /usr/local/include/ortools/sat/diffn.h
-- Installing: /usr/local/include/ortools/sat/clause.h
-- Installing: /usr/local/include/ortools/sat/sat_solver.h
-- Installing: /usr/local/include/ortools/sat/all_different.h
-- Installing: /usr/local/include/ortools/sat/go
-- Installing: /usr/local/include/ortools/sat/go/cp_solver_c.h
-- Installing: /usr/local/include/ortools/sat/cp_model_mapping.h
-- Installing: /usr/local/include/ortools/sat/encoding.h
-- Installing: /usr/local/include/ortools/sat/cp_model_loader.h
-- Installing: /usr/local/include/ortools/sat/cuts.h
-- Installing: /usr/local/include/ortools/sat/cp_model_expand.h
-- Installing: /usr/local/include/ortools/sat/linear_programming_constraint.h
-- Installing: /usr/local/include/ortools/sat/scheduling_cuts.h
-- Installing: /usr/local/include/ortools/sat/disjunctive.h
-- Installing: /usr/local/include/ortools/sat/model.h
-- Installing: /usr/local/include/ortools/sat/max_hs.h
-- Installing: /usr/local/include/ortools/sat/diffn_cuts.h
-- Installing: /usr/local/include/ortools/sat/csharp
-- Installing: /usr/local/include/ortools/sat/cp_model_lns.h
-- Installing: /usr/local/include/ortools/sat/probing.h
-- Installing: /usr/local/include/ortools/sat/python
-- Installing: /usr/local/include/ortools/sat/colab
-- Installing: /usr/local/include/ortools/sat/boolean_problem.h
-- Installing: /usr/local/include/ortools/sat/cumulative.h
-- Installing: /usr/local/include/ortools/sat/sat_cnf_reader.h
-- Installing: /usr/local/include/ortools/sat/integer.h
-- Installing: /usr/local/include/ortools/sat/simplification.h
-- Installing: /usr/local/include/ortools/sat/cp_model_symmetries.h
-- Installing: /usr/local/include/ortools/sat/var_domination.h
-- Installing: /usr/local/include/ortools/sat/presolve_util.h
-- Installing: /usr/local/include/ortools/sat/linear_propagation.h
-- Installing: /usr/local/include/ortools/sat/linear_constraint.h
-- Installing: /usr/local/include/ortools/sat/intervals.h
-- Installing: /usr/local/include/ortools/sat/lp_utils.h
-- Installing: /usr/local/include/ortools/sat/swig_helper.h
-- Installing: /usr/local/include/ortools/sat/linear_model.h
-- Installing: /usr/local/include/ortools/sat/work_assignment.h
-- Installing: /usr/local/include/ortools/sat/cumulative_energy.h
-- Installing: /usr/local/include/ortools/sat/cp_model_utils.h
-- Installing: /usr/local/include/ortools/sat/2d_orthogonal_packing.h
-- Installing: /usr/local/include/ortools/sat/cp_model_checker.h
-- Installing: /usr/local/include/ortools/sat/precedences.h
-- Installing: /usr/local/include/ortools/sat/constraint_violation.h
-- Installing: /usr/local/include/ortools/sat/java
-- Installing: /usr/local/include/ortools/sat/diffn_util.h
-- Installing: /usr/local/include/ortools/sat/optimization.h
-- Installing: /usr/local/include/ortools/sat/integer_search.h
-- Installing: /usr/local/include/ortools/sat/lb_tree_search.h
-- Installing: /usr/local/include/ortools/sat/linear_relaxation.h
-- Installing: /usr/local/include/ortools/sat/parameters_validation.h
-- Installing: /usr/local/include/ortools/sat/cp_model_solver.h
-- Installing: /usr/local/include/ortools/sat/sat_decision.h
-- Installing: /usr/local/include/ortools/sat/synchronization.h
-- Installing: /usr/local/include/ortools/sat/symmetry.h
-- Installing: /usr/local/include/ortools/sat/zero_half_cuts.h
-- Installing: /usr/local/include/ortools/sat/drat_writer.h
-- Installing: /usr/local/include/ortools/sat/cp_constraints.h
-- Installing: /usr/local/include/ortools/sat/implied_bounds.h
-- Installing: /usr/local/include/ortools/sat/sat_base.h
-- Installing: /usr/local/include/ortools/sat/drat_proof_handler.h
-- Installing: /usr/local/include/ortools/sat/cp_model_search.h
-- Installing: /usr/local/include/ortools/sat/linear_constraint_manager.h
-- Installing: /usr/local/include/ortools/sat/stat_tables.h
-- Installing: /usr/local/include/ortools/sat/presolve_context.h
-- Installing: /usr/local/include/ortools/sat/subsolver.h
-- Installing: /usr/local/include/ortools/sat/drat_checker.h
-- Installing: /usr/local/include/ortools/sat/inclusion.h
-- Installing: /usr/local/include/ortools/sat/integer_expr.h
-- Installing: /usr/local/include/ortools/sat/circuit.h
-- Installing: /usr/local/include/ortools/sat/sat_parameters.pb.h
-- Installing: /usr/local/include/ortools/sat/sat_inprocessing.h
-- Installing: /usr/local/include/ortools/algorithms
-- Installing: /usr/local/include/ortools/algorithms/set_cover.h
-- Installing: /usr/local/include/ortools/algorithms/find_graph_symmetries.h
-- Installing: /usr/local/include/ortools/algorithms/samples
-- Installing: /usr/local/include/ortools/algorithms/set_cover_invariant.h
-- Installing: /usr/local/include/ortools/algorithms/dynamic_permutation.h
-- Installing: /usr/local/include/ortools/algorithms/knapsack_solver.h
-- Installing: /usr/local/include/ortools/algorithms/knapsack_solver_for_cuts.h
-- Installing: /usr/local/include/ortools/algorithms/set_cover_model.h
-- Installing: /usr/local/include/ortools/algorithms/set_cover.pb.h
-- Installing: /usr/local/include/ortools/algorithms/sparse_permutation.h
-- Installing: /usr/local/include/ortools/algorithms/binary_indexed_tree.h
-- Installing: /usr/local/include/ortools/algorithms/dense_doubly_linked_list.h
-- Installing: /usr/local/include/ortools/algorithms/duplicate_remover.h
-- Installing: /usr/local/include/ortools/algorithms/csharp
-- Installing: /usr/local/include/ortools/algorithms/set_cover_reader.h
-- Installing: /usr/local/include/ortools/algorithms/python
-- Installing: /usr/local/include/ortools/algorithms/python/knapsack_solver_doc.h
-- Installing: /usr/local/include/ortools/algorithms/binary_search.h
-- Installing: /usr/local/include/ortools/algorithms/set_cover_utils.h
-- Installing: /usr/local/include/ortools/algorithms/hungarian.h
-- Installing: /usr/local/include/ortools/algorithms/dynamic_partition.h
-- Installing: /usr/local/include/ortools/algorithms/java
-- Installing: /usr/local/include/ortools/algorithms/radix_sort.h
-- Installing: /usr/local/include/ortools/algorithms/set_cover_mip.h
-- Installing: /usr/local/include/ortools/glpk
-- Installing: /usr/local/include/ortools/glpk/glpk_env_deleter.h
-- Installing: /usr/local/include/ortools/glpk/glpk_computational_form.h
-- Installing: /usr/local/include/ortools/glpk/glpk_formatters.h
-- Installing: /usr/local/include/ortools/base
-- Installing: /usr/local/include/ortools/base/gzipstring.h
-- Installing: /usr/local/include/ortools/base/murmur.h
-- Installing: /usr/local/include/ortools/base/options.h
-- Installing: /usr/local/include/ortools/base/gzipfile.h
-- Installing: /usr/local/include/ortools/base/adjustable_priority_queue-inl.h
-- Installing: /usr/local/include/ortools/base/path.h
-- Installing: /usr/local/include/ortools/base/top_n.h
-- Installing: /usr/local/include/ortools/base/macros.h
-- Installing: /usr/local/include/ortools/base/mathutil.h
-- Installing: /usr/local/include/ortools/base/iterator_adaptors.h
-- Installing: /usr/local/include/ortools/base/encodingutils.h
-- Installing: /usr/local/include/ortools/base/basictypes.h
-- Installing: /usr/local/include/ortools/base/numbers.h
-- Installing: /usr/local/include/ortools/base/memfile.h
-- Installing: /usr/local/include/ortools/base/stl_util.h
-- Installing: /usr/local/include/ortools/base/recordio.h
-- Installing: /usr/local/include/ortools/base/mutable_memfile.h
-- Installing: /usr/local/include/ortools/base/base_export.h
-- Installing: /usr/local/include/ortools/base/typeid.h
-- Installing: /usr/local/include/ortools/base/int_type.h
-- Installing: /usr/local/include/ortools/base/map_util.h
-- Installing: /usr/local/include/ortools/base/source_location.h
-- Installing: /usr/local/include/ortools/base/linked_hash_map.h
-- Installing: /usr/local/include/ortools/base/protoutil.h
-- Installing: /usr/local/include/ortools/base/bitmap.h
-- Installing: /usr/local/include/ortools/base/file.h
-- Installing: /usr/local/include/ortools/base/python-swig.h
-- Installing: /usr/local/include/ortools/base/message_matchers.h
-- Installing: /usr/local/include/ortools/base/container_logging.h
-- Installing: /usr/local/include/ortools/base/gmock.h
-- Installing: /usr/local/include/ortools/base/dynamic_library.h
-- Installing: /usr/local/include/ortools/base/accurate_sum.h
-- Installing: /usr/local/include/ortools/base/version.h
-- Installing: /usr/local/include/ortools/base/strtoint.h
-- Installing: /usr/local/include/ortools/base/status_macros.h
-- Installing: /usr/local/include/ortools/base/threadpool.h
-- Installing: /usr/local/include/ortools/base/dump_vars.h
-- Installing: /usr/local/include/ortools/base/small_map.h
-- Installing: /usr/local/include/ortools/base/status_matchers.h
-- Installing: /usr/local/include/ortools/base/sysinfo.h
-- Installing: /usr/local/include/ortools/base/logging.h
-- Installing: /usr/local/include/ortools/base/zipfile.h
-- Installing: /usr/local/include/ortools/base/hash.h
-- Installing: /usr/local/include/ortools/base/strong_int.h
-- Installing: /usr/local/include/ortools/base/strong_vector.h
-- Installing: /usr/local/include/ortools/base/case.h
-- Installing: /usr/local/include/ortools/base/filesystem.h
-- Installing: /usr/local/include/ortools/base/status_builder.h
-- Installing: /usr/local/include/ortools/base/timer.h
-- Installing: /usr/local/include/ortools/base/stl_logging.h
-- Installing: /usr/local/include/ortools/base/commandlineflags.h
-- Installing: /usr/local/include/ortools/base/parse_text_proto.h
-- Installing: /usr/local/include/ortools/base/types.h
-- Installing: /usr/local/include/ortools/base/protobuf_util.h
-- Installing: /usr/local/include/ortools/base/helpers.h
-- Installing: /usr/local/include/ortools/base/adjustable_priority_queue.h
-- Installing: /usr/local/include/ortools/base/init_google.h
-- Installing: /usr/local/include/ortools/base/ptr_util.h
-- Installing: /usr/local/include/ortools/constraint_solver
-- Installing: /usr/local/include/ortools/constraint_solver/search_limit.pb.h
-- Installing: /usr/local/include/ortools/constraint_solver/samples
-- Installing: /usr/local/include/ortools/constraint_solver/constraint_solveri.h
-- Installing: /usr/local/include/ortools/constraint_solver/routing_filters.h
-- Installing: /usr/local/include/ortools/constraint_solver/routing.h
-- Installing: /usr/local/include/ortools/constraint_solver/routing_parameters.h
-- Installing: /usr/local/include/ortools/constraint_solver/docs
-- Installing: /usr/local/include/ortools/constraint_solver/routing_index_manager.h
-- Installing: /usr/local/include/ortools/constraint_solver/routing_search.h
-- Installing: /usr/local/include/ortools/constraint_solver/solver_parameters.pb.h
-- Installing: /usr/local/include/ortools/constraint_solver/routing_lp_scheduling.h
-- Installing: /usr/local/include/ortools/constraint_solver/routing_parameters.pb.h
-- Installing: /usr/local/include/ortools/constraint_solver/csharp
-- Installing: /usr/local/include/ortools/constraint_solver/python
-- Installing: /usr/local/include/ortools/constraint_solver/routing_ils.pb.h
-- Installing: /usr/local/include/ortools/constraint_solver/demon_profiler.pb.h
-- Installing: /usr/local/include/ortools/constraint_solver/routing_decision_builders.h
-- Installing: /usr/local/include/ortools/constraint_solver/assignment.pb.h
-- Installing: /usr/local/include/ortools/constraint_solver/routing_insertion_lns.h
-- Installing: /usr/local/include/ortools/constraint_solver/routing_utils.h
-- Installing: /usr/local/include/ortools/constraint_solver/routing_enums.pb.h
-- Installing: /usr/local/include/ortools/constraint_solver/routing_types.h
-- Installing: /usr/local/include/ortools/constraint_solver/java
-- Installing: /usr/local/include/ortools/constraint_solver/java/javawrapcp_util.h
-- Installing: /usr/local/include/ortools/constraint_solver/constraint_solver.h
-- Installing: /usr/local/include/ortools/constraint_solver/routing_neighborhoods.h
-- Installing: /usr/local/include/ortools/constraint_solver/routing_ils.h
-- Installing: /usr/local/include/ortools/constraint_solver/search_stats.pb.h
-- Installing: /usr/local/include/ortools/constraint_solver/routing_constraints.h
-- Installing: /usr/local/include/ortools/java
-- Installing: /usr/local/include/ortools/java/com
-- Installing: /usr/local/include/ortools/java/com/google
-- Installing: /usr/local/include/ortools/java/com/google/ortools
-- Installing: /usr/local/include/ortools/java/com/google/ortools/constraintsolver
-- Installing: /usr/local/include/ortools/java/com/google/ortools/modelbuilder
-- Installing: /usr/local/include/ortools/java/com/google/ortools/sat
-- Installing: /usr/local/include/ortools/java/docs
-- Installing: /usr/local/include/ortools/lp_data
-- Installing: /usr/local/include/ortools/lp_data/lp_data_utils.h
-- Installing: /usr/local/include/ortools/lp_data/matrix_scaler.h
-- Installing: /usr/local/include/ortools/lp_data/lp_decomposer.h
-- Installing: /usr/local/include/ortools/lp_data/sparse_column.h
-- Installing: /usr/local/include/ortools/lp_data/sol_reader.h
-- Installing: /usr/local/include/ortools/lp_data/lp_types.h
-- Installing: /usr/local/include/ortools/lp_data/sparse.h
-- Installing: /usr/local/include/ortools/lp_data/lp_print_utils.h
-- Installing: /usr/local/include/ortools/lp_data/model_reader.h
-- Installing: /usr/local/include/ortools/lp_data/mps_reader.h
-- Installing: /usr/local/include/ortools/lp_data/sparse_vector.h
-- Installing: /usr/local/include/ortools/lp_data/lp_utils.h
-- Installing: /usr/local/include/ortools/lp_data/scattered_vector.h
-- Installing: /usr/local/include/ortools/lp_data/proto_utils.h
-- Installing: /usr/local/include/ortools/lp_data/permutation.h
-- Installing: /usr/local/include/ortools/lp_data/lp_parser.h
-- Installing: /usr/local/include/ortools/lp_data/lp_data.h
-- Installing: /usr/local/include/ortools/lp_data/sparse_row.h
-- Installing: /usr/local/include/ortools/lp_data/matrix_utils.h
-- Installing: /usr/local/include/ortools/lp_data/mps_reader_template.h
-- Installing: /usr/local/include/ortools/port
-- Installing: /usr/local/include/ortools/port/scoped_std_stream_capture.h
-- Installing: /usr/local/include/ortools/port/file.h
-- Installing: /usr/local/include/ortools/port/sysinfo.h
-- Installing: /usr/local/include/ortools/port/utf8.h
-- Installing: /usr/local/include/ortools/port/proto_utils.h
-- Installing: /usr/local/include/ortools/gurobi
-- Installing: /usr/local/include/ortools/gurobi/gurobi_util.h
-- Installing: /usr/local/include/ortools/gurobi/isv_public
-- Installing: /usr/local/include/ortools/gurobi/isv_public/gurobi_isv.h
-- Installing: /usr/local/include/ortools/gurobi/environment.h
-- Installing: /usr/local/include/ortools/pdlp
-- Installing: /usr/local/include/ortools/pdlp/quadratic_program.h
-- Installing: /usr/local/include/ortools/pdlp/trust_region.h
-- Installing: /usr/local/include/ortools/pdlp/test_util.h
-- Installing: /usr/local/include/ortools/pdlp/samples
-- Installing: /usr/local/include/ortools/pdlp/solve_log.pb.h
-- Installing: /usr/local/include/ortools/pdlp/primal_dual_hybrid_gradient.h
-- Installing: /usr/local/include/ortools/pdlp/solvers.pb.h
-- Installing: /usr/local/include/ortools/pdlp/sharded_optimization_utils.h
-- Installing: /usr/local/include/ortools/pdlp/sharded_quadratic_program.h
-- Installing: /usr/local/include/ortools/pdlp/solvers_proto_validation.h
-- Installing: /usr/local/include/ortools/pdlp/termination.h
-- Installing: /usr/local/include/ortools/pdlp/python
-- Installing: /usr/local/include/ortools/pdlp/sharder.h
-- Installing: /usr/local/include/ortools/pdlp/quadratic_program_io.h
-- Installing: /usr/local/include/ortools/pdlp/iteration_stats.h
-- Installing: /usr/local/include/ortools/xpress
-- Installing: /usr/local/include/ortools/xpress/environment.h
-- Installing: /usr/local/include/ortools/cpp
-- Installing: /usr/local/include/tpi
-- Installing: /usr/local/include/tpi/tpi_openmp.h
-- Installing: /usr/local/include/tpi/def_openmp.h
-- Installing: /usr/local/include/tpi/tpi.h
-- Installing: /usr/local/include/tpi/tpi_tnycthrd.h
-- Installing: /usr/local/include/tpi/type_tpi.h
-- Installing: /usr/local/include/tpi/type_tpi_tnycthrd.h
-- Installing: /usr/local/include/tpi/type_tpi_openmp.h
-- Installing: /usr/local/include/tpi/tpi_none.h
-- Installing: /usr/local/include/tpi/type_tpi_none.h
-- Up-to-date: /usr/local/bin
-- Installing: /usr/local/bin/sat_runner
-- Installing: /usr/local/bin/fzn-cp-sat
-- Installing: /usr/local/bin/protoc-25.3.0
-- Installing: /usr/local/bin/scip
-- Installing: /usr/local/bin/protoc
-- Installing: /usr/local/bin/solve
-- Installing: /usr/local/bin/vector_bin_packing
-- Installing: /usr/local/examples
-- Installing: /usr/local/examples/vrp_routes
-- Installing: /usr/local/examples/vrp_routes/CMakeLists.txt
-- Installing: /usr/local/examples/vrp_routes/vrp_routes.cc
-- Installing: /usr/local/examples/constraint_programming_cp
-- Installing: /usr/local/examples/constraint_programming_cp/constraint_programming_cp.cc
-- Installing: /usr/local/examples/constraint_programming_cp/CMakeLists.txt
-- Installing: /usr/local/examples/cp_is_fun_cp
-- Installing: /usr/local/examples/cp_is_fun_cp/CMakeLists.txt
-- Installing: /usr/local/examples/cp_is_fun_cp/cp_is_fun_cp.cc
-- Installing: /usr/local/examples/simple_glop_program
-- Installing: /usr/local/examples/simple_glop_program/CMakeLists.txt
-- Installing: /usr/local/examples/simple_glop_program/simple_glop_program.cc
-- Installing: /usr/local/examples/literal_sample_sat
-- Installing: /usr/local/examples/literal_sample_sat/CMakeLists.txt
-- Installing: /usr/local/examples/literal_sample_sat/literal_sample_sat.cc
-- Installing: /usr/local/examples/max_flow
-- Installing: /usr/local/examples/max_flow/CMakeLists.txt
-- Installing: /usr/local/examples/max_flow/max_flow.cc
-- Installing: /usr/local/examples/schedule_requests_sat
-- Installing: /usr/local/examples/schedule_requests_sat/schedule_requests_sat.cc
-- Installing: /usr/local/examples/schedule_requests_sat/CMakeLists.txt
-- Installing: /usr/local/examples/bfs_directed
-- Installing: /usr/local/examples/bfs_directed/CMakeLists.txt
-- Installing: /usr/local/examples/bfs_directed/bfs_directed.cc
-- Installing: /usr/local/examples/no_overlap_sample_sat
-- Installing: /usr/local/examples/no_overlap_sample_sat/CMakeLists.txt
-- Installing: /usr/local/examples/no_overlap_sample_sat/no_overlap_sample_sat.cc
-- Installing: /usr/local/examples/stop_after_n_solutions_sample_sat
-- Installing: /usr/local/examples/stop_after_n_solutions_sample_sat/CMakeLists.txt
-- Installing: /usr/local/examples/stop_after_n_solutions_sample_sat/stop_after_n_solutions_sample_sat.cc
-- Installing: /usr/local/examples/vrptw_store_solution_data
-- Installing: /usr/local/examples/vrptw_store_solution_data/CMakeLists.txt
-- Installing: /usr/local/examples/vrptw_store_solution_data/vrptw_store_solution_data.cc
-- Installing: /usr/local/examples/solve_with_time_limit_sample_sat
-- Installing: /usr/local/examples/solve_with_time_limit_sample_sat/solve_with_time_limit_sample_sat.cc
-- Installing: /usr/local/examples/solve_with_time_limit_sample_sat/CMakeLists.txt
-- Installing: /usr/local/examples/assumptions_sample_sat
-- Installing: /usr/local/examples/assumptions_sample_sat/assumptions_sample_sat.cc
-- Installing: /usr/local/examples/assumptions_sample_sat/CMakeLists.txt
-- Installing: /usr/local/examples/pdlp_solve
-- Installing: /usr/local/examples/pdlp_solve/CMakeLists.txt
-- Installing: /usr/local/examples/pdlp_solve/pdlp_solve.cc
-- Installing: /usr/local/examples/weighted_tardiness_sat
-- Installing: /usr/local/examples/weighted_tardiness_sat/weighted_tardiness_sat.cc
-- Installing: /usr/local/examples/weighted_tardiness_sat/CMakeLists.txt
-- Installing: /usr/local/examples/interval_sample_sat
-- Installing: /usr/local/examples/interval_sample_sat/CMakeLists.txt
-- Installing: /usr/local/examples/interval_sample_sat/interval_sample_sat.cc
-- Installing: /usr/local/examples/solve_and_print_intermediate_solutions_sample_sat
-- Installing: /usr/local/examples/solve_and_print_intermediate_solutions_sample_sat/solve_and_print_intermediate_solutions_sample_sat.cc
-- Installing: /usr/local/examples/solve_and_print_intermediate_solutions_sample_sat/CMakeLists.txt
-- Installing: /usr/local/examples/nqueens_sat
-- Installing: /usr/local/examples/nqueens_sat/nqueens_sat.cc
-- Installing: /usr/local/examples/nqueens_sat/CMakeLists.txt
-- Installing: /usr/local/examples/cvrptw_with_stop_times_and_resources
-- Installing: /usr/local/examples/cvrptw_with_stop_times_and_resources/CMakeLists.txt
-- Installing: /usr/local/examples/cvrptw_with_stop_times_and_resources/cvrptw_with_stop_times_and_resources.cc
-- Installing: /usr/local/examples/vrp_initial_routes
-- Installing: /usr/local/examples/vrp_initial_routes/vrp_initial_routes.cc
-- Installing: /usr/local/examples/vrp_initial_routes/CMakeLists.txt
-- Installing: /usr/local/examples/bool_or_sample_sat
-- Installing: /usr/local/examples/bool_or_sample_sat/bool_or_sample_sat.cc
-- Installing: /usr/local/examples/bool_or_sample_sat/CMakeLists.txt
-- Installing: /usr/local/examples/sports_scheduling_sat
-- Installing: /usr/local/examples/sports_scheduling_sat/CMakeLists.txt
-- Installing: /usr/local/examples/sports_scheduling_sat/sports_scheduling_sat.cc
-- Installing: /usr/local/examples/balance_min_flow
-- Installing: /usr/local/examples/balance_min_flow/CMakeLists.txt
-- Installing: /usr/local/examples/balance_min_flow/balance_min_flow.cc
-- Installing: /usr/local/examples/tsp_circuit_board
-- Installing: /usr/local/examples/tsp_circuit_board/CMakeLists.txt
-- Installing: /usr/local/examples/tsp_circuit_board/tsp_circuit_board.cc
-- Installing: /usr/local/examples/nurses_sat
-- Installing: /usr/local/examples/nurses_sat/nurses_sat.cc
-- Installing: /usr/local/examples/nurses_sat/CMakeLists.txt
-- Installing: /usr/local/examples/strawberry_fields_with_column_generation
-- Installing: /usr/local/examples/strawberry_fields_with_column_generation/strawberry_fields_with_column_generation.cc
-- Installing: /usr/local/examples/strawberry_fields_with_column_generation/CMakeLists.txt
-- Installing: /usr/local/examples/assignment_teams_sat
-- Installing: /usr/local/examples/assignment_teams_sat/CMakeLists.txt
-- Installing: /usr/local/examples/assignment_teams_sat/assignment_teams_sat.cc
-- Installing: /usr/local/examples/optional_interval_sample_sat
-- Installing: /usr/local/examples/optional_interval_sample_sat/CMakeLists.txt
-- Installing: /usr/local/examples/optional_interval_sample_sat/optional_interval_sample_sat.cc
-- Installing: /usr/local/examples/network_routing_sat
-- Installing: /usr/local/examples/network_routing_sat/network_routing_sat.cc
-- Installing: /usr/local/examples/network_routing_sat/CMakeLists.txt
-- Installing: /usr/local/examples/vrp_capacity
-- Installing: /usr/local/examples/vrp_capacity/CMakeLists.txt
-- Installing: /usr/local/examples/vrp_capacity/vrp_capacity.cc
-- Installing: /usr/local/examples/bin_packing_mip
-- Installing: /usr/local/examples/bin_packing_mip/bin_packing_mip.cc
-- Installing: /usr/local/examples/bin_packing_mip/CMakeLists.txt
-- Installing: /usr/local/examples/reified_sample_sat
-- Installing: /usr/local/examples/reified_sample_sat/reified_sample_sat.cc
-- Installing: /usr/local/examples/reified_sample_sat/CMakeLists.txt
-- Installing: /usr/local/examples/nurses_cp
-- Installing: /usr/local/examples/nurses_cp/nurses_cp.cc
-- Installing: /usr/local/examples/nurses_cp/CMakeLists.txt
-- Installing: /usr/local/examples/dijkstra_directed
-- Installing: /usr/local/examples/dijkstra_directed/dijkstra_directed.cc
-- Installing: /usr/local/examples/dijkstra_directed/CMakeLists.txt
-- Installing: /usr/local/examples/tsp
-- Installing: /usr/local/examples/tsp/tsp.cc
-- Installing: /usr/local/examples/tsp/CMakeLists.txt
-- Installing: /usr/local/examples/vrp_pickup_delivery_lifo
-- Installing: /usr/local/examples/vrp_pickup_delivery_lifo/vrp_pickup_delivery_lifo.cc
-- Installing: /usr/local/examples/vrp_pickup_delivery_lifo/CMakeLists.txt
-- Installing: /usr/local/examples/cp_is_fun_sat
-- Installing: /usr/local/examples/cp_is_fun_sat/CMakeLists.txt
-- Installing: /usr/local/examples/cp_is_fun_sat/cp_is_fun_sat.cc
-- Installing: /usr/local/examples/rabbits_and_pheasants_sat
-- Installing: /usr/local/examples/rabbits_and_pheasants_sat/rabbits_and_pheasants_sat.cc
-- Installing: /usr/local/examples/rabbits_and_pheasants_sat/CMakeLists.txt
-- Installing: /usr/local/examples/cvrptw_soft_capacity
-- Installing: /usr/local/examples/cvrptw_soft_capacity/cvrptw_soft_capacity.cc
-- Installing: /usr/local/examples/cvrptw_soft_capacity/CMakeLists.txt
-- Installing: /usr/local/examples/multiple_knapsack_mip
-- Installing: /usr/local/examples/multiple_knapsack_mip/CMakeLists.txt
-- Installing: /usr/local/examples/multiple_knapsack_mip/multiple_knapsack_mip.cc
-- Installing: /usr/local/examples/magic_sequence_sat
-- Installing: /usr/local/examples/magic_sequence_sat/CMakeLists.txt
-- Installing: /usr/local/examples/magic_sequence_sat/magic_sequence_sat.cc
-- Installing: /usr/local/examples/vrp_pickup_delivery
-- Installing: /usr/local/examples/vrp_pickup_delivery/CMakeLists.txt
-- Installing: /usr/local/examples/vrp_pickup_delivery/vrp_pickup_delivery.cc
-- Installing: /usr/local/examples/cvrptw_with_resources
-- Installing: /usr/local/examples/cvrptw_with_resources/cvrptw_with_resources.cc
-- Installing: /usr/local/examples/cvrptw_with_resources/CMakeLists.txt
-- Installing: /usr/local/examples/uncapacitated_facility_location
-- Installing: /usr/local/examples/uncapacitated_facility_location/CMakeLists.txt
-- Installing: /usr/local/examples/uncapacitated_facility_location/uncapacitated_facility_location.cc
-- Installing: /usr/local/examples/dijkstra_sequential
-- Installing: /usr/local/examples/dijkstra_sequential/CMakeLists.txt
-- Installing: /usr/local/examples/dijkstra_sequential/dijkstra_sequential.cc
-- Installing: /usr/local/examples/tsp_cities
-- Installing: /usr/local/examples/tsp_cities/tsp_cities.cc
-- Installing: /usr/local/examples/tsp_cities/CMakeLists.txt
-- Installing: /usr/local/examples/multiple_knapsack_sat
-- Installing: /usr/local/examples/multiple_knapsack_sat/CMakeLists.txt
-- Installing: /usr/local/examples/multiple_knapsack_sat/multiple_knapsack_sat.cc
-- Installing: /usr/local/examples/linear_programming
-- Installing: /usr/local/examples/linear_programming/CMakeLists.txt
-- Installing: /usr/local/examples/linear_programming/linear_programming.cc
-- Installing: /usr/local/examples/assignment_mip
-- Installing: /usr/local/examples/assignment_mip/CMakeLists.txt
-- Installing: /usr/local/examples/assignment_mip/assignment_mip.cc
-- Installing: /usr/local/examples/bfs_one_to_all
-- Installing: /usr/local/examples/bfs_one_to_all/bfs_one_to_all.cc
-- Installing: /usr/local/examples/bfs_one_to_all/CMakeLists.txt
-- Installing: /usr/local/examples/rabbits_and_pheasants_cp
-- Installing: /usr/local/examples/rabbits_and_pheasants_cp/CMakeLists.txt
-- Installing: /usr/local/examples/rabbits_and_pheasants_cp/rabbits_and_pheasants_cp.cc
-- Installing: /usr/local/examples/minimal_jobshop_sat
-- Installing: /usr/local/examples/minimal_jobshop_sat/minimal_jobshop_sat.cc
-- Installing: /usr/local/examples/minimal_jobshop_sat/CMakeLists.txt
-- Installing: /usr/local/examples/random_tsp
-- Installing: /usr/local/examples/random_tsp/random_tsp.cc
-- Installing: /usr/local/examples/random_tsp/CMakeLists.txt
-- Installing: /usr/local/examples/vrp_breaks
-- Installing: /usr/local/examples/vrp_breaks/vrp_breaks.cc
-- Installing: /usr/local/examples/vrp_breaks/CMakeLists.txt
-- Installing: /usr/local/examples/simple_lp_program
-- Installing: /usr/local/examples/simple_lp_program/simple_lp_program.cc
-- Installing: /usr/local/examples/simple_lp_program/CMakeLists.txt
-- Installing: /usr/local/examples/cvrptw_with_refueling
-- Installing: /usr/local/examples/cvrptw_with_refueling/cvrptw_with_refueling.cc
-- Installing: /usr/local/examples/cvrptw_with_refueling/CMakeLists.txt
-- Installing: /usr/local/examples/vector_bin_packing_solver
-- Installing: /usr/local/examples/vector_bin_packing_solver/vector_bin_packing_solver.cc
-- Installing: /usr/local/examples/vector_bin_packing_solver/CMakeLists.txt
-- Installing: /usr/local/examples/golomb_sat
-- Installing: /usr/local/examples/golomb_sat/CMakeLists.txt
-- Installing: /usr/local/examples/golomb_sat/golomb_sat.cc
-- Installing: /usr/local/examples/magic_square_sat
-- Installing: /usr/local/examples/magic_square_sat/CMakeLists.txt
-- Installing: /usr/local/examples/magic_square_sat/magic_square_sat.cc
-- Installing: /usr/local/examples/xpress_use
-- Installing: /usr/local/examples/xpress_use/CMakeLists.txt
-- Installing: /usr/local/examples/xpress_use/xpress_use.cc
-- Installing: /usr/local/examples/basic_example
-- Installing: /usr/local/examples/basic_example/basic_example.cc
-- Installing: /usr/local/examples/basic_example/CMakeLists.txt
-- Installing: /usr/local/examples/vrp
-- Installing: /usr/local/examples/vrp/vrp.cc
-- Installing: /usr/local/examples/vrp/CMakeLists.txt
-- Installing: /usr/local/examples/nqueens_cp
-- Installing: /usr/local/examples/nqueens_cp/nqueens_cp.cc
-- Installing: /usr/local/examples/nqueens_cp/CMakeLists.txt
-- Installing: /usr/local/examples/nqueens
-- Installing: /usr/local/examples/nqueens/nqueens.cc
-- Installing: /usr/local/examples/nqueens/CMakeLists.txt
-- Installing: /usr/local/examples/multi_knapsack_sat
-- Installing: /usr/local/examples/multi_knapsack_sat/CMakeLists.txt
-- Installing: /usr/local/examples/multi_knapsack_sat/multi_knapsack_sat.cc
-- Installing: /usr/local/examples/assignment_teams_mip
-- Installing: /usr/local/examples/assignment_teams_mip/CMakeLists.txt
-- Installing: /usr/local/examples/assignment_teams_mip/assignment_teams_mip.cc
-- Installing: /usr/local/examples/ranking_sample_sat
-- Installing: /usr/local/examples/ranking_sample_sat/ranking_sample_sat.cc
-- Installing: /usr/local/examples/ranking_sample_sat/CMakeLists.txt
-- Installing: /usr/local/examples/knapsack_2d_sat
-- Installing: /usr/local/examples/knapsack_2d_sat/CMakeLists.txt
-- Installing: /usr/local/examples/knapsack_2d_sat/knapsack_2d_sat.cc
-- Installing: /usr/local/examples/simple_cp_program
-- Installing: /usr/local/examples/simple_cp_program/simple_cp_program.cc
-- Installing: /usr/local/examples/simple_cp_program/CMakeLists.txt
-- Installing: /usr/local/examples/dijkstra_all_pairs_shortest_paths
-- Installing: /usr/local/examples/dijkstra_all_pairs_shortest_paths/CMakeLists.txt
-- Installing: /usr/local/examples/dijkstra_all_pairs_shortest_paths/dijkstra_all_pairs_shortest_paths.cc
-- Installing: /usr/local/examples/jobshop_sat
-- Installing: /usr/local/examples/jobshop_sat/jobshop_sat.cc
-- Installing: /usr/local/examples/jobshop_sat/CMakeLists.txt
-- Installing: /usr/local/examples/earliness_tardiness_cost_sample_sat
-- Installing: /usr/local/examples/earliness_tardiness_cost_sample_sat/CMakeLists.txt
-- Installing: /usr/local/examples/earliness_tardiness_cost_sample_sat/earliness_tardiness_cost_sample_sat.cc
-- Installing: /usr/local/examples/clone_model_sample_sat
-- Installing: /usr/local/examples/clone_model_sample_sat/clone_model_sample_sat.cc
-- Installing: /usr/local/examples/clone_model_sample_sat/CMakeLists.txt
-- Installing: /usr/local/examples/assignment_sat
-- Installing: /usr/local/examples/assignment_sat/assignment_sat.cc
-- Installing: /usr/local/examples/assignment_sat/CMakeLists.txt
-- Installing: /usr/local/examples/flow_api
-- Installing: /usr/local/examples/flow_api/CMakeLists.txt
-- Installing: /usr/local/examples/flow_api/flow_api.cc
-- Installing: /usr/local/examples/assignment_groups_sat
-- Installing: /usr/local/examples/assignment_groups_sat/assignment_groups_sat.cc
-- Installing: /usr/local/examples/assignment_groups_sat/CMakeLists.txt
-- Installing: /usr/local/examples/cvrptw_with_precedences
-- Installing: /usr/local/examples/cvrptw_with_precedences/cvrptw_with_precedences.cc
-- Installing: /usr/local/examples/cvrptw_with_precedences/CMakeLists.txt
-- Installing: /usr/local/examples/tsp_cities_routes
-- Installing: /usr/local/examples/tsp_cities_routes/tsp_cities_routes.cc
-- Installing: /usr/local/examples/tsp_cities_routes/CMakeLists.txt
-- Installing: /usr/local/examples/simple_mip_program
-- Installing: /usr/local/examples/simple_mip_program/simple_mip_program.cc
-- Installing: /usr/local/examples/simple_mip_program/CMakeLists.txt
-- Installing: /usr/local/examples/dobble_ls
-- Installing: /usr/local/examples/dobble_ls/dobble_ls.cc
-- Installing: /usr/local/examples/dobble_ls/CMakeLists.txt
-- Installing: /usr/local/examples/vrp_drop_nodes
-- Installing: /usr/local/examples/vrp_drop_nodes/vrp_drop_nodes.cc
-- Installing: /usr/local/examples/vrp_drop_nodes/CMakeLists.txt
-- Installing: /usr/local/examples/frequency_assignment_problem
-- Installing: /usr/local/examples/frequency_assignment_problem/frequency_assignment_problem.cc
-- Installing: /usr/local/examples/frequency_assignment_problem/CMakeLists.txt
-- Installing: /usr/local/examples/assignment_groups_mip
-- Installing: /usr/local/examples/assignment_groups_mip/CMakeLists.txt
-- Installing: /usr/local/examples/assignment_groups_mip/assignment_groups_mip.cc
-- Installing: /usr/local/examples/bfs_undirected
-- Installing: /usr/local/examples/bfs_undirected/CMakeLists.txt
-- Installing: /usr/local/examples/bfs_undirected/bfs_undirected.cc
-- Installing: /usr/local/examples/costas_array_sat
-- Installing: /usr/local/examples/costas_array_sat/costas_array_sat.cc
-- Installing: /usr/local/examples/costas_array_sat/CMakeLists.txt
-- Installing: /usr/local/examples/simple_pdlp_program
-- Installing: /usr/local/examples/simple_pdlp_program/simple_pdlp_program.cc
-- Installing: /usr/local/examples/simple_pdlp_program/CMakeLists.txt
-- Installing: /usr/local/examples/cvrptw_with_breaks
-- Installing: /usr/local/examples/cvrptw_with_breaks/cvrptw_with_breaks.cc
-- Installing: /usr/local/examples/cvrptw_with_breaks/CMakeLists.txt
-- Installing: /usr/local/examples/integer_programming_example
-- Installing: /usr/local/examples/integer_programming_example/integer_programming_example.cc
-- Installing: /usr/local/examples/integer_programming_example/CMakeLists.txt
-- Installing: /usr/local/examples/integer_programming
-- Installing: /usr/local/examples/integer_programming/integer_programming.cc
-- Installing: /usr/local/examples/integer_programming/CMakeLists.txt
-- Installing: /usr/local/examples/vrp_solution_callback
-- Installing: /usr/local/examples/vrp_solution_callback/vrp_solution_callback.cc
-- Installing: /usr/local/examples/vrp_solution_callback/CMakeLists.txt
-- Installing: /usr/local/examples/assignment_task_sizes_sat
-- Installing: /usr/local/examples/assignment_task_sizes_sat/CMakeLists.txt
-- Installing: /usr/local/examples/assignment_task_sizes_sat/assignment_task_sizes_sat.cc
-- Installing: /usr/local/examples/knapsack
-- Installing: /usr/local/examples/knapsack/CMakeLists.txt
-- Installing: /usr/local/examples/knapsack/knapsack.cc
-- Installing: /usr/local/examples/pdptw
-- Installing: /usr/local/examples/pdptw/pdptw.cc
-- Installing: /usr/local/examples/pdptw/CMakeLists.txt
-- Installing: /usr/local/examples/cp_sat_example
-- Installing: /usr/local/examples/cp_sat_example/CMakeLists.txt
-- Installing: /usr/local/examples/cp_sat_example/cp_sat_example.cc
-- Installing: /usr/local/examples/simple_knapsack_program
-- Installing: /usr/local/examples/simple_knapsack_program/simple_knapsack_program.cc
-- Installing: /usr/local/examples/simple_knapsack_program/CMakeLists.txt
-- Installing: /usr/local/examples/channeling_sample_sat
-- Installing: /usr/local/examples/channeling_sample_sat/channeling_sample_sat.cc
-- Installing: /usr/local/examples/channeling_sample_sat/CMakeLists.txt
-- Installing: /usr/local/examples/cvrp_disjoint_tw
-- Installing: /usr/local/examples/cvrp_disjoint_tw/cvrp_disjoint_tw.cc
-- Installing: /usr/local/examples/cvrp_disjoint_tw/CMakeLists.txt
-- Installing: /usr/local/examples/dag_simple_shortest_path
-- Installing: /usr/local/examples/dag_simple_shortest_path/dag_simple_shortest_path.cc
-- Installing: /usr/local/examples/dag_simple_shortest_path/CMakeLists.txt
-- Installing: /usr/local/examples/course_scheduling_run
-- Installing: /usr/local/examples/course_scheduling_run/CMakeLists.txt
-- Installing: /usr/local/examples/course_scheduling_run/course_scheduling_run.cc
-- Installing: /usr/local/examples/vrp_resources
-- Installing: /usr/local/examples/vrp_resources/vrp_resources.cc
-- Installing: /usr/local/examples/vrp_resources/CMakeLists.txt
-- Installing: /usr/local/examples/linear_solver_protocol_buffers
-- Installing: /usr/local/examples/linear_solver_protocol_buffers/CMakeLists.txt
-- Installing: /usr/local/examples/linear_solver_protocol_buffers/linear_solver_protocol_buffers.cc
-- Installing: /usr/local/examples/cvrptw
-- Installing: /usr/local/examples/cvrptw/CMakeLists.txt
-- Installing: /usr/local/examples/cvrptw/cvrptw.cc
-- Installing: /usr/local/examples/dimacs_assignment
-- Installing: /usr/local/examples/dimacs_assignment/CMakeLists.txt
-- Installing: /usr/local/examples/dimacs_assignment/dimacs_assignment.cc
-- Installing: /usr/local/examples/search_for_all_solutions_sample_sat
-- Installing: /usr/local/examples/search_for_all_solutions_sample_sat/search_for_all_solutions_sample_sat.cc
-- Installing: /usr/local/examples/search_for_all_solutions_sample_sat/CMakeLists.txt
-- Installing: /usr/local/examples/linear_programming_example
-- Installing: /usr/local/examples/linear_programming_example/linear_programming_example.cc
-- Installing: /usr/local/examples/linear_programming_example/CMakeLists.txt
-- Installing: /usr/local/examples/dijkstra_one_to_all
-- Installing: /usr/local/examples/dijkstra_one_to_all/dijkstra_one_to_all.cc
-- Installing: /usr/local/examples/dijkstra_one_to_all/CMakeLists.txt
-- Installing: /usr/local/examples/vrp_pickup_delivery_fifo
-- Installing: /usr/local/examples/vrp_pickup_delivery_fifo/vrp_pickup_delivery_fifo.cc
-- Installing: /usr/local/examples/vrp_pickup_delivery_fifo/CMakeLists.txt
-- Installing: /usr/local/examples/assignment_task_sizes_mip
-- Installing: /usr/local/examples/assignment_task_sizes_mip/assignment_task_sizes_mip.cc
-- Installing: /usr/local/examples/assignment_task_sizes_mip/CMakeLists.txt
-- Installing: /usr/local/examples/binpacking_2d_sat
-- Installing: /usr/local/examples/binpacking_2d_sat/binpacking_2d_sat.cc
-- Installing: /usr/local/examples/binpacking_2d_sat/CMakeLists.txt
-- Installing: /usr/local/examples/simple_min_cost_flow_program
-- Installing: /usr/local/examples/simple_min_cost_flow_program/simple_min_cost_flow_program.cc
-- Installing: /usr/local/examples/simple_min_cost_flow_program/CMakeLists.txt
-- Installing: /usr/local/examples/stigler_diet
-- Installing: /usr/local/examples/stigler_diet/stigler_diet.cc
-- Installing: /usr/local/examples/stigler_diet/CMakeLists.txt
-- Installing: /usr/local/examples/min_cost_flow
-- Installing: /usr/local/examples/min_cost_flow/min_cost_flow.cc
-- Installing: /usr/local/examples/min_cost_flow/CMakeLists.txt
-- Installing: /usr/local/examples/vrp_starts_ends
-- Installing: /usr/local/examples/vrp_starts_ends/CMakeLists.txt
-- Installing: /usr/local/examples/vrp_starts_ends/vrp_starts_ends.cc
-- Installing: /usr/local/examples/assignment_linear_sum_assignment
-- Installing: /usr/local/examples/assignment_linear_sum_assignment/assignment_linear_sum_assignment.cc
-- Installing: /usr/local/examples/assignment_linear_sum_assignment/CMakeLists.txt
-- Installing: /usr/local/examples/assignment_min_flow
-- Installing: /usr/local/examples/assignment_min_flow/assignment_min_flow.cc
-- Installing: /usr/local/examples/assignment_min_flow/CMakeLists.txt
-- Installing: /usr/local/examples/shift_minimization_sat
-- Installing: /usr/local/examples/shift_minimization_sat/CMakeLists.txt
-- Installing: /usr/local/examples/shift_minimization_sat/shift_minimization_sat.cc
-- Installing: /usr/local/examples/step_function_sample_sat
-- Installing: /usr/local/examples/step_function_sample_sat/CMakeLists.txt
-- Installing: /usr/local/examples/step_function_sample_sat/step_function_sample_sat.cc
-- Installing: /usr/local/examples/dijkstra_undirected
-- Installing: /usr/local/examples/dijkstra_undirected/dijkstra_undirected.cc
-- Installing: /usr/local/examples/dijkstra_undirected/CMakeLists.txt
-- Installing: /usr/local/examples/vrp_with_time_limit
-- Installing: /usr/local/examples/vrp_with_time_limit/vrp_with_time_limit.cc
-- Installing: /usr/local/examples/vrp_with_time_limit/CMakeLists.txt
-- Installing: /usr/local/examples/minimal_jobshop_cp
-- Installing: /usr/local/examples/minimal_jobshop_cp/minimal_jobshop_cp.cc
-- Installing: /usr/local/examples/minimal_jobshop_cp/CMakeLists.txt
-- Installing: /usr/local/examples/slitherlink_sat
-- Installing: /usr/local/examples/slitherlink_sat/CMakeLists.txt
-- Installing: /usr/local/examples/slitherlink_sat/slitherlink_sat.cc
-- Installing: /usr/local/examples/simple_ls_program
-- Installing: /usr/local/examples/simple_ls_program/simple_ls_program.cc
-- Installing: /usr/local/examples/simple_ls_program/CMakeLists.txt
-- Installing: /usr/local/examples/tsp_distance_matrix
-- Installing: /usr/local/examples/tsp_distance_matrix/tsp_distance_matrix.cc
-- Installing: /usr/local/examples/tsp_distance_matrix/CMakeLists.txt
-- Installing: /usr/local/examples/dag_shortest_path_sequential
-- Installing: /usr/local/examples/dag_shortest_path_sequential/dag_shortest_path_sequential.cc
-- Installing: /usr/local/examples/dag_shortest_path_sequential/CMakeLists.txt
-- Installing: /usr/local/examples/qap_sat
-- Installing: /usr/local/examples/qap_sat/CMakeLists.txt
-- Installing: /usr/local/examples/qap_sat/qap_sat.cc
-- Installing: /usr/local/examples/variable_intervals_sat
-- Installing: /usr/local/examples/variable_intervals_sat/variable_intervals_sat.cc
-- Installing: /usr/local/examples/variable_intervals_sat/CMakeLists.txt
-- Installing: /usr/local/examples/mps_driver
-- Installing: /usr/local/examples/mps_driver/CMakeLists.txt
-- Installing: /usr/local/examples/mps_driver/mps_driver.cc
-- Installing: /usr/local/examples/simple_max_flow_program
-- Installing: /usr/local/examples/simple_max_flow_program/CMakeLists.txt
-- Installing: /usr/local/examples/simple_max_flow_program/simple_max_flow_program.cc
-- Installing: /usr/local/examples/mip_var_array
-- Installing: /usr/local/examples/mip_var_array/mip_var_array.cc
-- Installing: /usr/local/examples/mip_var_array/CMakeLists.txt
-- Installing: /usr/local/examples/solution_hinting_sample_sat
-- Installing: /usr/local/examples/solution_hinting_sample_sat/solution_hinting_sample_sat.cc
-- Installing: /usr/local/examples/solution_hinting_sample_sat/CMakeLists.txt
-- Installing: /usr/local/examples/simple_sat_program
-- Installing: /usr/local/examples/simple_sat_program/simple_sat_program.cc
-- Installing: /usr/local/examples/simple_sat_program/CMakeLists.txt
-- Installing: /usr/local/examples/simple_routing_program
-- Installing: /usr/local/examples/simple_routing_program/simple_routing_program.cc
-- Installing: /usr/local/examples/simple_routing_program/CMakeLists.txt
-- Installing: /usr/local/examples/vrp_time_windows
-- Installing: /usr/local/examples/vrp_time_windows/CMakeLists.txt
-- Installing: /usr/local/examples/vrp_time_windows/vrp_time_windows.cc
-- Installing: /usr/local/examples/course_scheduling
-- Installing: /usr/local/examples/course_scheduling/course_scheduling.cc
-- Installing: /usr/local/examples/course_scheduling/CMakeLists.txt
-- Installing: /usr/local/examples/dag_shortest_path_one_to_all
-- Installing: /usr/local/examples/dag_shortest_path_one_to_all/CMakeLists.txt
-- Installing: /usr/local/examples/dag_shortest_path_one_to_all/dag_shortest_path_one_to_all.cc
-- Installing: /usr/local/examples/cryptarithm_sat
-- Installing: /usr/local/examples/cryptarithm_sat/cryptarithm_sat.cc
-- Installing: /usr/local/examples/cryptarithm_sat/CMakeLists.txt
-- Installing: /usr/local/examples/binpacking_problem_sat
-- Installing: /usr/local/examples/binpacking_problem_sat/binpacking_problem_sat.cc
-- Installing: /usr/local/examples/binpacking_problem_sat/CMakeLists.txt
-- Installing: /usr/local/examples/cvrptw_with_time_dependent_costs
-- Installing: /usr/local/examples/cvrptw_with_time_dependent_costs/cvrptw_with_time_dependent_costs.cc
-- Installing: /usr/local/examples/cvrptw_with_time_dependent_costs/CMakeLists.txt
-- Installing: /usr/local/examples/non_linear_sat
-- Installing: /usr/local/examples/non_linear_sat/non_linear_sat.cc
-- Installing: /usr/local/examples/non_linear_sat/CMakeLists.txt
-- Installing: /usr/local/examples/vrp_global_span
-- Installing: /usr/local/examples/vrp_global_span/vrp_global_span.cc
-- Installing: /usr/local/examples/vrp_global_span/CMakeLists.txt
-- Installing: /usr/local/examples/linear_assignment_api
-- Installing: /usr/local/examples/linear_assignment_api/linear_assignment_api.cc
-- Installing: /usr/local/examples/linear_assignment_api/CMakeLists.txt
-- Installing: /usr/local/Makefile
-- Installing: /usr/local/README.md
-- Installing: /usr/local/lib/libsteering_functions.so
-- Installing: /usr/local/include/matplot/detail/exports.h
-- Installing: /usr/local/lib/libFields2Cover.so
-- Set runtime path of "/usr/local/lib/libFields2Cover.so" to ""
-- Up-to-date: /usr/local/lib/libsteering_functions.so
-- Installing: /usr/local/lib/libmatplot.so.1.2.0
-- Installing: /usr/local/lib/libmatplot.so.1
-- Installing: /usr/local/lib/libmatplot.so
-- Up-to-date: /usr/local/include
-- Installing: /usr/local/include/fields2cover.h
-- Installing: /usr/local/include/fields2cover
-- Installing: /usr/local/include/fields2cover/swath_generator
-- Installing: /usr/local/include/fields2cover/swath_generator/brute_force.h
-- Installing: /usr/local/include/fields2cover/swath_generator/swath_generator_base.h
-- Installing: /usr/local/include/fields2cover/headland_generator
-- Installing: /usr/local/include/fields2cover/headland_generator/constant_headland.h
-- Installing: /usr/local/include/fields2cover/headland_generator/headland_generator_base.h
-- Installing: /usr/local/include/fields2cover/path_planning
-- Installing: /usr/local/include/fields2cover/path_planning/dubins_curves.h
-- Installing: /usr/local/include/fields2cover/path_planning/reeds_shepp_curves_hc.h
-- Installing: /usr/local/include/fields2cover/path_planning/reeds_shepp_curves.h
-- Installing: /usr/local/include/fields2cover/path_planning/dubins_curves_cc.h
-- Installing: /usr/local/include/fields2cover/path_planning/path_planning.h
-- Installing: /usr/local/include/fields2cover/path_planning/steer_to_path.hpp
-- Installing: /usr/local/include/fields2cover/path_planning/turning_base.h
-- Installing: /usr/local/include/fields2cover/decomposition
-- Installing: /usr/local/include/fields2cover/decomposition/decomposition_base.h
-- Installing: /usr/local/include/fields2cover/decomposition/trapezoidal_decomp.h
-- Installing: /usr/local/include/fields2cover/decomposition/boustrophedon_decomp.h
-- Installing: /usr/local/include/fields2cover/route_planning
-- Installing: /usr/local/include/fields2cover/route_planning/boustrophedon_order.h
-- Installing: /usr/local/include/fields2cover/route_planning/snake_order.h
-- Installing: /usr/local/include/fields2cover/route_planning/route_planner_base.h
-- Installing: /usr/local/include/fields2cover/route_planning/spiral_order.h
-- Installing: /usr/local/include/fields2cover/route_planning/custom_order.h
-- Installing: /usr/local/include/fields2cover/route_planning/single_cell_swaths_order_base.h
-- Installing: /usr/local/include/fields2cover/utils
-- Installing: /usr/local/include/fields2cover/utils/spline.h
-- Installing: /usr/local/include/fields2cover/utils/parser.h
-- Installing: /usr/local/include/fields2cover/utils/visualizer.h
-- Installing: /usr/local/include/fields2cover/utils/transformation.h
-- Installing: /usr/local/include/fields2cover/utils/random.h
-- Installing: /usr/local/include/fields2cover/types
-- Installing: /usr/local/include/fields2cover/types/Route.h
-- Installing: /usr/local/include/fields2cover/types/Geometries_impl.hpp
-- Installing: /usr/local/include/fields2cover/types/MultiPoint.h
-- Installing: /usr/local/include/fields2cover/types/Geometries.h
-- Installing: /usr/local/include/fields2cover/types/LinearRing.h
-- Installing: /usr/local/include/fields2cover/types/Geometry.h
-- Installing: /usr/local/include/fields2cover/types/Cell.h
-- Installing: /usr/local/include/fields2cover/types/Robot.h
-- Installing: /usr/local/include/fields2cover/types/Path.h
-- Installing: /usr/local/include/fields2cover/types/Cells.h
-- Installing: /usr/local/include/fields2cover/types/PathState.h
-- Installing: /usr/local/include/fields2cover/types/Field.h
-- Installing: /usr/local/include/fields2cover/types/Geometry_impl.hpp
-- Installing: /usr/local/include/fields2cover/types/MultiLineString.h
-- Installing: /usr/local/include/fields2cover/types/Swath.h
-- Installing: /usr/local/include/fields2cover/types/Point.h
-- Installing: /usr/local/include/fields2cover/types/Graph.h
-- Installing: /usr/local/include/fields2cover/types/Strip.h
-- Installing: /usr/local/include/fields2cover/types/Graph2D.h
-- Installing: /usr/local/include/fields2cover/types/SwathsByCells.h
-- Installing: /usr/local/include/fields2cover/types/Swaths.h
-- Installing: /usr/local/include/fields2cover/types/LineString.h
-- Installing: /usr/local/include/fields2cover/types.h
-- Installing: /usr/local/include/fields2cover/objectives
-- Installing: /usr/local/include/fields2cover/objectives/hg_obj
-- Installing: /usr/local/include/fields2cover/objectives/hg_obj/hg_objective.h
-- Installing: /usr/local/include/fields2cover/objectives/hg_obj/rem_area.h
-- Installing: /usr/local/include/fields2cover/objectives/pp_obj
-- Installing: /usr/local/include/fields2cover/objectives/pp_obj/path_length.h
-- Installing: /usr/local/include/fields2cover/objectives/pp_obj/pp_objective.h
-- Installing: /usr/local/include/fields2cover/objectives/rp_obj
-- Installing: /usr/local/include/fields2cover/objectives/rp_obj/rp_objective.h
-- Installing: /usr/local/include/fields2cover/objectives/rp_obj/complete_turn_path_obj.h
-- Installing: /usr/local/include/fields2cover/objectives/rp_obj/direct_dist_path_obj.h
-- Installing: /usr/local/include/fields2cover/objectives/sg_obj
-- Installing: /usr/local/include/fields2cover/objectives/sg_obj/field_coverage.h
-- Installing: /usr/local/include/fields2cover/objectives/sg_obj/swath_length.h
-- Installing: /usr/local/include/fields2cover/objectives/sg_obj/n_swath_modified.h
-- Installing: /usr/local/include/fields2cover/objectives/sg_obj/overlaps.h
-- Installing: /usr/local/include/fields2cover/objectives/sg_obj/n_swath.h
-- Installing: /usr/local/include/fields2cover/objectives/sg_obj/sg_objective.h
-- Installing: /usr/local/include/fields2cover/objectives/decomp_obj
-- Installing: /usr/local/include/fields2cover/objectives/decomp_obj/decomp_objective.h
-- Installing: /usr/local/include/fields2cover/objectives/base_objective.h
-- Installing: /usr/local/lib/cmake/Fields2Cover/Fields2CoverConfig.cmake
-- Installing: /usr/local/lib/cmake/Fields2Cover/Fields2CoverConfigVersion.cmake
-- Installing: /usr/local/lib/cmake/Fields2Cover/Fields2CoverTargets.cmake
-- Installing: /usr/local/lib/cmake/Fields2Cover/Fields2CoverTargets-release.cmake
/root/Fields2Cover/build/swig/python/setup.py:2: DeprecationWarning: The distutils package is deprecated and slated for removal in Python 3.12. Use setuptools or check PEP 632 for potential alternatives
  from distutils.sysconfig import get_python_lib
/root/Fields2Cover/build/swig/python/setup.py:2: DeprecationWarning: The distutils.sysconfig module is deprecated, use sysconfig instead
  from distutils.sysconfig import get_python_lib
running install
/usr/lib/python3/dist-packages/setuptools/command/install.py:34: SetuptoolsDeprecationWarning: setup.py install is deprecated. Use build and pip and other standards-based tools.
  warnings.warn(
  [02_f2c] 环境指纹 -> /root/agriautolab/evidence/env_f2c.json（其内容哈希已在证据链：RecordedCsvAdapter.env_hash）
  [03_python] venv 就绪（封闭 + F2C binding 已拷入）✓
  ✅ Ubuntu 22.04
  ✅ Python 3.10.12
  ✅ LANG 含 UTF-8（当前 C.UTF-8）
  ✅ 原生文件系统
  ✅ shapely 2.1.2 / GEOS 3.13.1（与 env_geometry.json 一致）
  ✅ pip 依赖与 requirements.lock 一致
  ✅ import fields2cover 成功，commit=3613525c…
  ✅ 无 CRLF 文件（.gitattributes eol=lf）
  ✅ pytest -q → 530 passed, 30 skipped in 3.32s
——
全部通过 ✅
== 安装完成。激活：source .venv/bin/activate ==
EXIT_CODE=0

const config = {
  title: 'DHIDB',
  tagline: 'Global habitat dynamics, queried where you need them',
  favicon: 'img/DHIDB_logo.png',
  url: 'https://thisistaimur.github.io',
  baseUrl: '/dhidb/',
  organizationName: 'thisistaimur',
  projectName: 'dhidb',
  onBrokenLinks: 'throw',
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },
  presets: [
    [
      'classic',
      {
        docs: {
          routeBasePath: '/',
          sidebarPath: require.resolve('./sidebars.js'),
          showLastUpdateTime: false,
          breadcrumbs: false,
        },
        blog: false,
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      },
    ],
  ],
  themeConfig: {
    image: 'img/DHIDB_logo.png',
    colorMode: {
      defaultMode: 'dark',
      respectPrefersColorScheme: false,
    },
    navbar: {
      logo: {
        alt: 'DHIDB logo',
        src: 'img/DHIDB_logo_white.png',
        srcDark: 'img/DHIDB_logo.png',
      },
      items: [
        {to: '/getting-started', label: 'Getting started', position: 'left'},
        {to: '/data-model', label: 'Data model', position: 'left'},
        {to: '/queries', label: 'Queries', position: 'left'},
        {to: '/quality', label: 'Quality', position: 'left'},
        {to: '/api', label: 'Python API', position: 'left'},
        {to: '/contributing', label: 'Contributing', position: 'left'},
        {
          href: 'https://pypi.org/project/dhidb/',
          label: 'PyPI',
          position: 'right',
        },
        {
          href: 'https://github.com/thisistaimur/dhidb',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      copyright:
        'Copyright © 2026 <a href="https://www.ufz.de/">Helmholtz Centre for Environmental Research - UFZ</a>. Developed by <a href="https://thisistaimur.me/">Taimur Khan</a>.',
    },
    prism: {
      theme: require('prism-react-renderer').themes.github,
      darkTheme: require('prism-react-renderer').themes.dracula,
    },
  },
};

module.exports = config;

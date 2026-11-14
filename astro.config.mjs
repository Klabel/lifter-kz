// astro.config.mjs

import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://lifter.kz', // Замените на ваш реальный домен!
  integrations: [
    tailwind(),
    // Карта сайта: дата обновления = дата сборки, чтобы поисковики видели свежие изменения
    sitemap({
      changefreq: 'weekly',
      lastmod: new Date(),
      serialize(item) {
        const path = new URL(item.url).pathname;
        if (path === '/') item.priority = 1.0;
        else if (['/parts/', '/repair/', '/tires/', '/catalog/'].includes(path)) item.priority = 0.9;
        else item.priority = 0.7;
        return item;
      },
    }),
  ],
});
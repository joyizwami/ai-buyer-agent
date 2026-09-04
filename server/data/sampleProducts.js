const sampleProducts = [
  {
    id: 'product1',
    url: 'https://rukminim1.flixcart.com/image/200/200/khf63680/cases-covers/back-cover/d/7/g/spigen-acs02256-original-imafxfgbffqaugur.jpeg?q=70',
    detailUrl: '',
    title: {
      shortTitle: 'Mobile Covers',
      longTitle: 'Spigen Mobile Cover for Premium Protection'
    },
    price: {
      mrp: 1499,
      cost: 899,
      discount: '40%'
    },
    quantity: 10,
    description: 'Premium mobile cover designed for durability and modern style.',
    discount: 'Extra 10% Off',
    tagline: 'Deal of the day'
  },
  {
    id: 'product2',
    url: 'https://rukminim1.flixcart.com/image/200/200/k5lcvbk0/moisturizer-cream/9/w/g/600-body-lotion-aloe-hydration-for-normal-skin-nivea-lotion-original-imafz8jb3ftt8gf9.jpeg?q=70',
    detailUrl: '',
    title: {
      shortTitle: 'Skin & Hair Care',
      longTitle: 'Nivea Aloe Hydration Body Lotion for Normal Skin'
    },
    price: {
      mrp: 899,
      cost: 549,
      discount: '39%'
    },
    quantity: 12,
    description: 'Hydrating lotion for soft, refreshed skin with aloe and vitamins.',
    discount: 'From 99+5% Off',
    tagline: 'Shampoos, Face Washes & More'
  },
  {
    id: 'product3',
    url: 'https://rukminim1.flixcart.com/flap/200/200/image/74bc985c62f19245.jpeg?q=70',
    detailUrl: '',
    title: {
      shortTitle: 'Skybags & Safari',
      longTitle: 'Safari and Skybags Travel Collection'
    },
    price: {
      mrp: 2999,
      cost: 1499,
      discount: '50%'
    },
    quantity: 9,
    description: 'Smart and durable backpacks and luggage for everyday travel.',
    discount: 'Upto 70% Off',
    tagline: 'Deal of the Day'
  },
  {
    id: 'product4',
    url: 'https://rukminim1.flixcart.com/image/300/300/kll7bm80/smartwatch/c/1/n/43-mo-sw-sense-500-android-ios-molife-original-imagyzyycnpujyjh.jpeg?q=70',
    detailUrl: 'https://rukminim1.flixcart.com/image/416/416/kll7bm80/smartwatch/c/1/n/43-mo-sw-sense-500-android-ios-molife-original-imagyzyycnpujyjh.jpeg?q=70',
    title: {
      shortTitle: 'Smart Watches',
      longTitle: 'Molife Sense 500 Smartwatch  (Black Strap, Freesize)'
    },
    price: {
      mrp: 6999,
      cost: 4049,
      discount: '42%'
    },
    quantity: 7,
    description: 'The Molife Sense 500, a brilliant smartwatch with a beautiful large display. Say hello to the infinity 1.7-inch display with 2.5D curved edges. Thanks to seamless Bluetooth 5.0 connectivity, you wont have to keep waiting. Bring a change to your outfit every day with changeable straps. A splash of color every day keeps the boredom away.',
    discount: 'Grab Now',
    tagline: 'Best Seller'
  },
  {
    id: 'product5',
    url: 'https://rukminim1.flixcart.com/flap/150/150/image/b616a7aa607d3be0.jpg?q=70',
    detailUrl: '',
    title: {
      shortTitle: 'Sports & Fitness Essentials',
      longTitle: 'A complete range of sports and fitness accessories'
    },
    price: {
      mrp: 1999,
      cost: 999,
      discount: '50%'
    },
    quantity: 14,
    description: 'Fitness essentials for gym, home workouts, and active routines.',
    discount: 'Upto 80% Off',
    tagline: 'Ab Exerciser, Yoga & more'
  },
  {
    id: 'product6',
    url: 'https://rukminim1.flixcart.com/image/300/300/ke7ff680/hammock-swing/j/f/u/q3-jkaf-y3l0-furniture-kart-original-imafux96kpy7grch.jpeg?q=70',
    detailUrl: '',
    title: {
      shortTitle: 'Hammock And Swings',
      longTitle: 'Hammock And Swings for a Relaxed Outdoor Setup'
    },
    price: {
      mrp: 2499,
      cost: 1199,
      discount: '52%'
    },
    quantity: 8,
    description: 'Comfortable hammock swing ideal for balconies, patios, and lounges.',
    discount: 'From ₹199',
    tagline: 'Trendy Collection'
  },
  {
    id: 'product-headphones',
    url: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=300&q=80',
    detailUrl: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80',
    title: {
      shortTitle: 'Wireless Headphones',
      longTitle: 'Sony Wireless Noise-Canceling Headphones'
    },
    price: {
      mrp: 29999,
      cost: 24999,
      discount: '17%'
    },
    quantity: 10,
    description: 'Wireless over-ear headphones with active noise cancellation and rich audio.',
    discount: 'AI Pick',
    tagline: 'Under ₹25,000'
  },
  {
    id: 'product7',
    url: 'https://rukminim1.flixcart.com/image/200/200/k3lwuq80/mobile/f/y/q/apple-iphone-11-mhdc3hn-a-original-imafmhh9y7hpzefx.jpeg?q=70',
    detailUrl: 'https://rukminim1.flixcart.com/image/416/416/k3lwuq80/mobile/f/y/q/apple-iphone-11-mhdc3hn-a-original-imafmhh9y7hpzefx.jpeg?q=70',
    title: { shortTitle: 'Mobiles', longTitle: 'Apple iPhone 11 (Black, 128 GB)' },
    price: { mrp: 54900, cost: 42999, discount: '22%' },
    quantity: 15,
    description: 'A powerful smartphone with a dual-camera system, all-day battery life, and Apple performance.',
    discount: 'Bank Offer',
    tagline: 'Popular Mobile'
  },
  {
    id: 'product8',
    url: 'https://rukminim1.flixcart.com/image/200/200/k2jbyq80pkq/j7gi8w0/mobile/5/y/u/mi-redmi-note-8-pro-mzb81h3in-original-imafgfe5q7k6h9xc.jpeg?q=70',
    detailUrl: 'https://rukminim1.flixcart.com/image/416/416/k2jbyq80pkq/j7gi8w0/mobile/5/y/u/mi-redmi-note-8-pro-mzb81h3in-original-imafgfe5q7k6h9xc.jpeg?q=70',
    title: { shortTitle: 'Mobiles', longTitle: 'Redmi Note 8 Pro (Shadow Black, 128 GB)' },
    price: { mrp: 18999, cost: 14999, discount: '21%' },
    quantity: 18,
    description: 'A performance-focused smartphone with a 64MP quad-camera setup and smooth gaming experience.',
    discount: 'Extra ₹1000 Off',
    tagline: 'Best Value'
  },
  {
    id: 'product9',
    url: 'https://rukminim1.flixcart.com/image/200/200/k7w8eq80/mobile/h/q/x/realme-x2-pro-rmx1931-original-imafq3yg5d6j9gcy.jpeg?q=70',
    detailUrl: 'https://rukminim1.flixcart.com/image/416/416/k7w8eq80/mobile/h/q/x/realme-x2-pro-rmx1931-original-imafq3yg5d6j9gcy.jpeg?q=70',
    title: { shortTitle: 'Mobiles', longTitle: 'Realme X2 Pro (Neon Blue, 128 GB)' },
    price: { mrp: 35999, cost: 28999, discount: '19%' },
    quantity: 12,
    description: 'Premium display and excellent camera performance in a sleek mid-range flagship design.',
    discount: 'Limited Period',
    tagline: 'Trending'
  },
  {
    id: 'product10',
    url: 'https://rukminim1.flixcart.com/image/200/200/k7gikcw0/mobile/g/8/a/samsung-galaxy-m31s-sm-m317fzkdins-original-imafphx7cug9ehbn.jpeg?q=70',
    detailUrl: 'https://rukminim1.flixcart.com/image/416/416/k7gikcw0/mobile/g/8/a/samsung-galaxy-m31s-sm-m317fzkdins-original-imafphx7cug9ehbn.jpeg?q=70',
    title: { shortTitle: 'Mobiles', longTitle: 'Samsung Galaxy M31s (Mirage Blue, 128 GB)' },
    price: { mrp: 24999, cost: 19999, discount: '20%' },
    quantity: 16,
    description: 'Large battery, cinematic display, and reliable performance for everyday use.',
    discount: 'No Cost EMI',
    tagline: 'Top Pick'
  },
  {
    id: 'product11',
    url: 'https://rukminim1.flixcart.com/image/200/200/kb5e2kw0/mobile/2/a/p/samsung-galaxy-f12-6gb-128gb-sm-f127gzsgins-original-imafsk7h7d4dfyvb.jpeg?q=70',
    detailUrl: 'https://rukminim1.flixcart.com/image/416/416/kb5e2kw0/mobile/2/a/p/samsung-galaxy-f12-6gb-128gb-sm-f127gzsgins-original-imafsk7h7d4dfyvb.jpeg?q=70',
    title: { shortTitle: 'Mobiles', longTitle: 'Samsung Galaxy F12 (Sky Blue, 64 GB)' },
    price: { mrp: 14999, cost: 10999, discount: '27%' },
    quantity: 20,
    description: 'Battery-first smartphone with a big screen and multiple camera lenses for versatile shots.',
    discount: 'Flat ₹1000 Off',
    tagline: 'Popular'
  },
  {
    id: 'product12',
    url: 'https://rukminim1.flixcart.com/image/200/200/kq4oqq80/mobile/k/w/a/iphone-12-mini-mlk93hn-a-original-imag48zmdk4en4ha.jpeg?q=70',
    detailUrl: 'https://rukminim1.flixcart.com/image/416/416/kq4oqq80/mobile/k/w/a/iphone-12-mini-mlk93hn-a-original-imag48zmdk4en4ha.jpeg?q=70',
    title: { shortTitle: 'Mobiles', longTitle: 'Apple iPhone 12 Mini (White, 64 GB)' },
    price: { mrp: 59900, cost: 49999, discount: '16%' },
    quantity: 11,
    description: 'Compact iPhone with premium build quality, 5G support, and excellent camera results.',
    discount: 'Special Price',
    tagline: 'Apple Choice'
  },
  {
    id: 'product13',
    url: 'https://rukminim1.flixcart.com/image/200/200/k1b5g7k0/mobile/q/x/x/vivo-v20-pro-v2030-original-imafh4x6g7c3m8sp.jpeg?q=70',
    detailUrl: 'https://rukminim1.flixcart.com/image/416/416/k1b5g7k0/mobile/q/x/x/vivo-v20-pro-v2030-original-imafh4x6g7c3m8sp.jpeg?q=70',
    title: { shortTitle: 'Mobiles', longTitle: 'Vivo V20 Pro (Sunset Melody, 128 GB)' },
    price: { mrp: 33999, cost: 27999, discount: '17%' },
    quantity: 9,
    description: 'A stylish mid-range phone with a sleek camera setup, smooth performance, and sleek design.',
    discount: 'Best Deal',
    tagline: 'Camera Focus'
  },
  {
    id: 'product14',
    url: 'https://rukminim1.flixcart.com/image/200/200/klz1yfk0/mobile/r/2/0/poco-m3-c3kq-original-imagzzf7n8p7dtwr.jpeg?q=70',
    detailUrl: 'https://rukminim1.flixcart.com/image/416/416/klz1yfk0/mobile/r/2/0/poco-m3-c3kq-original-imagzzf7n8p7dtwr.jpeg?q=70',
    title: { shortTitle: 'Mobiles', longTitle: 'POCO M3 (Cool Blue, 64 GB)' },
    price: { mrp: 13999, cost: 9999, discount: '28%' },
    quantity: 22,
    description: 'A budget gaming smartphone with a powerful battery and smooth multitasking performance.',
    discount: 'Mobile Fest',
    tagline: 'Gaming Choice'
  },
  {
    id: 'product15',
    url: 'https://rukminim1.flixcart.com/image/200/200/kk2mrww0/mobile/q/u/y/oneplus-nord-ce-5g-5011100302-original-imafzf9m3p7rf9wu.jpeg?q=70',
    detailUrl: 'https://rukminim1.flixcart.com/image/416/416/kk2mrww0/mobile/q/u/y/oneplus-nord-ce-5g-5011100302-original-imafzf9m3p7rf9wu.jpeg?q=70',
    title: { shortTitle: 'Mobiles', longTitle: 'OnePlus Nord CE 5G (Blue Void, 128 GB)' },
    price: { mrp: 27999, cost: 22999, discount: '17%' },
    quantity: 10,
    description: 'Fast 5G connectivity and premium software experience in a sleek modern smartphone design.',
    discount: 'Extra Offer',
    tagline: '5G Ready'
  },
  {
    id: 'product16',
    url: 'https://rukminim1.flixcart.com/image/200/200/ktn9pjk0/mobile/d/n/f/infinix-hot-12-play-x6817-original-imag6y6whhy9m5gp.jpeg?q=70',
    detailUrl: 'https://rukminim1.flixcart.com/image/416/416/ktn9pjk0/mobile/d/n/f/infinix-hot-12-play-x6817-original-imag6y6whhy9m5gp.jpeg?q=70',
    title: { shortTitle: 'Mobiles', longTitle: 'Infinix Hot 12 Play (Racing Black, 64 GB)' },
    price: { mrp: 12999, cost: 8999, discount: '30%' },
    quantity: 18,
    description: 'Budget-friendly smartphone with big battery life and a vibrant display for everyday tasks.',
    discount: 'Weekend Offer',
    tagline: 'Affordable'
  },
  {
    id: 'product17',
    url: 'https://rukminim1.flixcart.com/image/200/200/k9loccw0/mobile/6/8/y/realme-narzo-20-rrmz2011-original-imafrcfgrmzhx7tx.jpeg?q=70',
    detailUrl: 'https://rukminim1.flixcart.com/image/416/416/k9loccw0/mobile/6/8/y/realme-narzo-20-rrmz2011-original-imafrcfgrmzhx7tx.jpeg?q=70',
    title: { shortTitle: 'Mobiles', longTitle: 'Realme Narzo 20 (Glory Silver, 64 GB)' },
    price: { mrp: 15999, cost: 11999, discount: '25%' },
    quantity: 14,
    description: 'A value-packed phone with a large battery, strong design, and efficient performance.',
    discount: 'Special Discount',
    tagline: 'Popular'
  },
  {
    id: 'product18',
    url: 'https://rukminim1.flixcart.com/image/200/200/l1v1uvk0/mobile/7/2/3/-original-imagdc5hxcudkb23.jpeg?q=70',
    detailUrl: 'https://rukminim1.flixcart.com/image/416/416/l1v1uvk0/mobile/7/2/3/-original-imagdc5hxcudkb23.jpeg?q=70',
    title: { shortTitle: 'Mobiles', longTitle: 'Motorola G60 (Moonless, 128 GB)' },
    price: { mrp: 17999, cost: 14999, discount: '17%' },
    quantity: 13,
    description: 'A reliable mid-range phone with a clean Android experience and long battery endurance.',
    discount: 'Limited Price',
    tagline: 'Trust Choice'
  }
];

export default sampleProducts;

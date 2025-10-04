/*
 Simple frontend mock layer to enable demo without backend.
 Activated when REACT_APP_MOCK=true at build/runtime.
*/

(function initDemoMock() {
  try {
    const mockFlag = ((typeof process !== 'undefined' && process && process.env && process.env.REACT_APP_MOCK) || (typeof window !== 'undefined' && window.REACT_APP_MOCK));
    const isMock = String((mockFlag ?? 'true')).toLowerCase() === 'true';
    if (!isMock) return;

    const originalFetch = window.fetch.bind(window);
    const originalWebSocket = window.WebSocket;
    const XHROpen = window.XMLHttpRequest && window.XMLHttpRequest.prototype.open;
    const XHRSend = window.XMLHttpRequest && window.XMLHttpRequest.prototype.send;

    const delay = (ms) => new Promise((res) => setTimeout(res, ms));
    const jsonResponse = (body, init = {}) => {
      return new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' }, ...init });
    };

    const demoTravelId = '68dd74bcaafe454913a15d54';
    const demoUserId = '684737965d4056e12086a134';
    const nowIso = () => new Date().toISOString();

    function buildMockBodyFor(path, method, searchParams, bodyText) {
      // Auth
      if (path.endsWith('/api/auth/token') && method === 'POST') {
        return { status: 200, body: { access_token: 'demo-token', token_type: 'bearer' } };
      }
      if (path.endsWith('/api/auth/me') && method === 'GET') {
        return { status: 200, body: { id: demoUserId, email: 'demo@user.com', name: 'Demo User' } };
      }

      // Travels root
      if (path === '/api/travels' || path === '/api/travels/') {
        if (method === 'GET') {
          return { status: 200, body: [
            {
              _id: demoTravelId,
              id: demoTravelId,
              title: 'Trip to thailand',
              destination: 'thailand',
              user_id: demoUserId,
              total_days: 14,
              created_at: '2025-10-01T18:36:44.786Z',
              updated_at: '2025-10-01T18:41:48.727Z'
            }
          ] };
        }
        if (method === 'POST') {
          return { status: 200, body: {
            _id: demoTravelId,
            id: demoTravelId,
            title: 'Trip to thailand',
            destination: 'thailand',
            user_id: demoUserId,
            total_days: 14,
            created_at: '2025-10-01T18:36:44.786Z',
            updated_at: '2025-10-01T18:41:48.727Z'
          } };
        }
      }

      // Specific travel dependent endpoints
      const travelMatch = path.match(/\/api\/travels\/([^\/]+)/);
      const travelId = travelMatch ? travelMatch[1] : demoTravelId;

      if (path.endsWith(`/api/travels/${travelId}/chat`) && method === 'GET') {
        return { status: 200, body: [
          {
            id: 'mock-ack-1',
            content: "Your 14-day Thailand trip request has been registered. Would you prefer a relaxed, cultural, or adventurous trip?",
            is_user: false,
            timestamp: '2025-10-01T18:39:00.000Z',
            user_id: 'assistant',
            travel_id: travelId
          },
          {
            id: '68dd7616aafe454913a15d55',
            content: "We'd like a very cultural trip",
            is_user: true,
            timestamp: '2025-10-01T18:39:20.000Z',
            user_id: demoUserId,
            travel_id: travelId
          },
          {
            id: 'mock-assistant-proposal-14d',
            content: `# 14-Day Cultural Thailand Itinerary (Draft)

## Bangkok (Days 1-3)
• **Day 1-3: Bangkok** — Grand Palace, Wat Pho, Chao Phraya canals, Chinatown, floating markets
• Explore royal temples and traditional architecture
• Experience local street food and vibrant nightlife

## Ayutthaya (Days 4-6)  
• **Day 4-6: Ayutthaya** — Historical park (UNESCO), cycling among ancient temples, river cruise
• Discover the former capital's magnificent ruins
• Bike tours through less-visited temple complexes

## Sukhothai (Days 7-9)
• **Day 7-9: Sukhothai** — Historical Park (UNESCO), cycling among ruins, local crafts workshops
• Visit Thailand's first capital and its iconic Buddha statues
• Learn traditional Thai handicrafts from local artisans

## Chiang Mai (Days 10-12)
• **Day 10-12: Chiang Mai** — Doi Suthep temple, Old City exploration, ethical Elephant sanctuary, Doi Inthanon National Park
• Experience northern Thai culture and cuisine
• Visit ethical elephant sanctuaries and mountain temples

## Chiang Rai (Days 13-14)
• **Day 13-14: Chiang Rai** — White Temple (Wat Rong Khun), Blue Temple (Wat Rong Suea Ten), local markets
• Discover contemporary Thai art and architecture
• Explore the Golden Triangle region

---

**Note:** This cultural-focused itinerary emphasizes historical sites, temples, and traditional experiences. If you prefer adjustments (e.g., more beach time, different cities), let me know and I'll adapt the plan accordingly.`,
            is_user: false,
            timestamp: '2025-10-01T18:39:50.000Z',
            user_id: 'assistant',
            travel_id: travelId
          },
          {
            id: 'mock-user-add-beach-2',
            content: "We'd like to end with beach days, please.",
            is_user: true,
            timestamp: '2025-10-01T18:40:20.000Z',
            user_id: demoUserId,
            travel_id: travelId
          },
          {
            id: 'mock-final-en',
            content: `# Thailand Trip Itinerary: Bangkok, Ayutthaya, Sukhothai, Chiang Mai, and Phuket

## Bangkok
**Day 1: Bangkok - 10/01/2025 6:42 PM to 10/04/2025 6:42 PM**

• **6:42 PM** - Arrival at Suvarnabhumi Airport (BKK), transfer to the hotel Mandarin Hotel Managed by Centre Point, Sukhumvit (address: 662 Sukhumvit Rd, Khlong Toei, Bangkok 10110). Check-in and rest.

• **8:00 PM** - Dinner at Cabbages & Condoms (Sukhumvit Soi 12), a restaurant with authentic Thai food and a themed atmosphere, known for supporting social causes.

**Day 2: Bangkok**

• **8:00 AM** - Breakfast at the hotel.

• **9:00 AM** - Visit the Grand Palace and Wat Phra Kaew (Temple of the Emerald Buddha), address Na Phra Lan Rd, Phra Nakhon. Early entry recommended to avoid crowds and heat.

• **12:30 PM** - Lunch at Thip Samai Pad Thai (313 Maha Chai Rd), one of the best places to try authentic Pad Thai.

• **2:00 PM** - Tour of Wat Pho (Temple of the Reclining Buddha), address 2 Sanamchai Rd, Phra Nakhon. Don't miss the traditional Thai massage here.

• **4:30 PM** - Boat ride on the Chao Phraya River and canals, with a stop at Wat Arun (Temple of Dawn).

• **7:00 PM** - Dinner and nightlife on Khao San Road, a vibrant area with bars, restaurants, and street stalls.

**Day 3: Bangkok**

• **8:00 AM** - Breakfast at the hotel.

• **9:00 AM** - Visit Chatuchak Market (weekends only) or Taling Chan Floating Market (for a quieter local experience).

• **12:30 PM** - Lunch at Som Tam Nua (392/14 Siam Square Soi 5), famous for papaya salad and Isaan food.

• **2:00 PM** - Visit the Mahanakhon SkyWalk, for panoramic city views (address 114 Naradhiwas Rajanagarindra Rd).

• **4:00 PM** - Tour of Chinatown (Yaowarat), exploring temples, markets, and street stalls.

• **7:00 PM** - Dinner at Raan Jay Fai (327 Maha Chai Rd), famous for Michelin-starred street food.

**Transportation:** 10/04 6:42 PM - Train journey to Ayutthaya (approx. 1 hr 30 min). Transfer to Baan Tye Wang Guesthouse, 20/2 U Thong Rd.

---

## Ayutthaya
**Day 4: Ayutthaya - 10/04/2025 8:12 PM to 10/06/2025 8:12 PM**

• **8:00 AM** - Breakfast at the guesthouse.

• **9:00 AM** - Visit the Ayutthaya Historical Park (UNESCO), including Wat Mahathat, Wat Ratchaburana, and Wat Phra Si Sanphet.

• **12:30 PM** - Lunch at Malakor Kitchen and Cafe.

• **2:00 PM** - Bike tour of the ruins and less-touristy temples.

• **5:00 PM** - Boat ride on the Chao Phraya River for panoramic views.

• **7:00 PM** - Dinner at Raan Tha Luang, specializing in local food.

**Day 5: Ayutthaya**

• **8:00 AM** - Breakfast.

• **9:00 AM** - Visit the Chao Sam Phraya National Museum to understand the kingdom's history.

• **12:00 PM** - Lunch at Coffee Old City.

• **2:00 PM** - Visit Wat Phra Ram Temple and the Ayothaya Floating Market.

• **5:00 PM** - Rest at a local cafe.

• **7:00 PM** - Dinner at Baan Kao Nhom, for desserts and light dishes.

**Transportation:** 10/06 8:12 PM - Bus journey to Sukhothai (approx. 4 hrs). Transfer to Sukhothai Heritage Resort.

---

## Sukhothai
**Day 6: Sukhothai - 10/07/2025 12:12 AM to 10/09/2025 12:12 AM**

• **8:00 AM** - Breakfast at the hotel.

• **9:00 AM** - Visit Sukhothai Historical Park (UNESCO), including Wat Mahathat, Wat Si Chum, and Wat Sa Si.

• **12:30 PM** - Lunch at local restaurant near the park.

• **2:00 PM** - Bike tour through the ancient ruins and temple complexes.

• **5:00 PM** - Visit the Ramkhamhaeng National Museum to learn about the kingdom's history.

• **7:00 PM** - Dinner at local restaurant with traditional northern Thai cuisine.

**Day 7: Sukhothai**

• **8:00 AM** - Breakfast at the hotel.

• **9:00 AM** - Visit Si Satchanalai Historical Park, a UNESCO World Heritage site with well-preserved ruins.

• **12:30 PM** - Lunch at local restaurant.

• **2:00 PM** - Traditional Thai handicraft workshop (pottery or silk weaving).

• **5:00 PM** - Return to Sukhothai and relax.

• **7:00 PM** - Dinner at hotel restaurant.

**Transportation:** 10/09 12:12 AM - Bus journey to Chiang Mai (approx. 5 hrs). Transfer to Yaang Come Village, 90/3 Sridonchai Road.

---

## Chiang Mai
**Day 8: Chiang Mai - 10/09/2025 5:12 AM to 10/12/2025 5:12 AM**

• **8:00 AM** - Breakfast at the hotel.

• **9:00 AM** - Visit Wat Phra That Doi Suthep Temple, located on the mountain with city views. Entrance: 50 THB.

• **12:30 PM** - Lunch at Khao Soi Khun Yai, to try the famous northern curry Khao Soi.

• **2:00 PM** - Tour of the Old City, visiting Wat Chedi Luang and Wat Phra Singh.

• **5:00 PM** - Traditional Thai massage at Fah Lanna Spa.

• **7:00 PM** - Dinner at The Riverside Bar & Restaurant, Thai food and live music.

**Day 9: Chiang Mai**

• **7:00 AM** - Full-day excursion to Elephant Nature Park (ethical elephant sanctuary and nature reserve).

• **12:30 PM** - Lunch included at the park.

• **5:00 PM** - Return to Chiang Mai.

• **7:00 PM** - Dinner at SP Chicken, specializing in local-style chicken.

• **Optional:** Visit the Chiang Mai Night Bazaar for shopping and snacks.

**Day 10: Chiang Mai**

• **8:00 AM** - Breakfast at the hotel.

• **9:00 AM** - Cultural tour and light trekking through Doi Inthanon National Park, the highest point in Thailand.

• **1:00 PM** - Lunch at a local restaurant within the park.

• **4:00 PM** - Return to the city and rest.

• **7:00 PM** - Dinner at Dash! Restaurant and Bar, in a traditional Thai house.

**Transportation:** 10/12 5:12 AM - Flight to Phuket (approx. 2 hrs). Transfer to The Marina Phuket Hotel, 72/1 Yaowarat Rd, near Patong Beach.

---

## Phuket
**Day 11: Phuket - 10/12/2025 7:12 AM to 10/15/2025 7:12 AM**

• **9:00 AM** - Breakfast at the hotel.

• **10:00 AM** - Beach day at Patong Beach, with optional water sports.

• **1:00 PM** - Lunch at No.9 2nd Restaurant, Thai food and fresh seafood.

• **3:00 PM** - Visit the Big Buddha of Phuket and Wat Chalong Temple.

• **7:00 PM** - Dinner at Baan Rim Pa, a restaurant with sea views and fine Thai dining.

• **9:00 PM** - Visit Bangla Road for vibrant nightlife.

**Day 12: Phuket**

• **7:00 AM** - Boat excursion to the Phi Phi Islands (includes snorkeling, visits to Maya Bay, Bamboo Island).

• **12:30 PM** - Picnic lunch on the island.

• **5:00 PM** - Return to Phuket and rest.

• **7:00 PM** - Light dinner at a local restaurant near the hotel or the Phuket Town night market.

**Day 13: Phuket**

• **8:00 AM** - Breakfast at the hotel.

• **9:00 AM** - Visit Phuket Old Town, Sino-Portuguese architecture and cafes.

• **12:00 PM** - Lunch at One Chun Café & Restaurant.

• **2:00 PM** - Relaxation at Kata or Karon Beach.

• **4:00 PM** - Thai massage at Oasis Spa Phuket.

• **7:00 PM** - Dinner at Suay Restaurant, contemporary Thai cuisine.

**Day 14: Phuket - Departure**

• **5:00 AM** - Departure to Phuket Airport (approx. 30 min).

• **7:00 AM** - Return flight or connection according to itinerary.

---

## General Tips

**Weather:** October marks the end of the monsoon season; expect occasional rain and warm temperatures (28−33°C).

**Transportation:** Use Grab taxis in cities; internal flights recommended for long distances (Bangkok-Chiang Mai, Chiang Mai-Phuket).

**Currency Exchange:** Best to exchange at official banks or reliable exchange houses.

**Cultural Respect:** When visiting temples, wear appropriate clothing (shoulders and knees covered).

**Hydration:** Always carry water and sunscreen.

---

## Estimated Budget (per person)

• **Accommodation:** $40-70 USD per night (3-4 star hotels) ≈ $560 - $980
• **Meals:** $10-20 USD per day ≈ $140 - $280
• **Internal Transportation:** (flights, trains, taxis) ≈ $150 - $250
• **Entrance Fees and Tours:** ≈ $100 - $150
• **Total Approximate:** $950 - $1660 USD`,
            is_user: false,
            timestamp: '2025-10-01T18:41:00.000Z',
            user_id: 'assistant',
            travel_id: travelId
          }
        ] };
      }

      if (path.endsWith(`/api/travels/${travelId}/itinerary`) && method === 'GET') {
        return { status: 200, body: [
          {
            id: 'it-1',
            travel_id: travelId,
            country: 'thailand',
            cities: [
              { 
                name: 'Bangkok', 
                arrival_dt: '2025-10-01T18:42:00Z',
                departure_dt: '2025-10-04T18:42:00Z',
                coordinates: { latitude: 13.7524938, longitude: 100.4935089 }
              },
              { 
                name: 'Ayutthaya', 
                arrival_dt: '2025-10-04T20:12:00Z',
                departure_dt: '2025-10-06T20:12:00Z',
                coordinates: { latitude: 14.3535427, longitude: 100.5645684 }
              },
              { 
                name: 'Sukhothai', 
                arrival_dt: '2025-10-07T00:12:00Z',
                departure_dt: '2025-10-09T00:12:00Z',
                coordinates: { latitude: 17.006139, longitude: 99.823307 }
              },
              { 
                name: 'Chiang Mai', 
                arrival_dt: '2025-10-09T05:12:00Z',
                departure_dt: '2025-10-12T05:12:00Z',
                coordinates: { latitude: 18.787493, longitude: 98.9672428 }
              },
              { 
                name: 'Phuket', 
                arrival_dt: '2025-10-12T07:12:00Z',
                departure_dt: '2025-10-15T07:12:00Z',
                coordinates: { latitude: 7.9366015, longitude: 98.3529292 }
              }
            ],
            generated_at: nowIso(),
          }
        ] };
      }

      if (path.endsWith(`/api/travels/${travelId}/hotels/suggestions`) && method === 'GET') {
        return { status: 200, body: {
          travel_id: travelId,
          suggestions: [
            {
              city: 'Bangkok',
              check_in: '2025-10-01',
              check_out: '2025-10-04',
              nights: 3,
              hotels: [
                {
                  city: 'Bangkok',
                  name: 'Mandarin Oriental Bangkok',
                  area: 'Riverside',
                  price_tier: 'premium',
                  notes: 'Hotel histórico de lujo con vistas al Chao Phraya.',
                  image_url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Mandarin_Oriental_Bangkok_Bang_Rak.jpg/960px-Mandarin_Oriental_Bangkok_Bang_Rak.jpg',
                  deeplink_url: '#'
                },
                {
                  city: 'Bangkok',
                  name: 'Siam Kempinski Hotel Bangkok',
                  area: 'Siam',
                  price_tier: 'premium',
                  notes: 'Junto a centros comerciales y BTS.',
                  image_url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Kempinski_Logo_2015.svg/640px-Kempinski_Logo_2015.svg.png',
                  deeplink_url: '#'
                },
                {
                  city: 'Bangkok',
                  name: 'Amara Bangkok',
                  area: 'Silom',
                  price_tier: 'mid',
                  notes: 'Moderno con piscina en azotea.',
                  image_url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/Bangkok_Montage_2024_2.jpg/960px-Bangkok_Montage_2024_2.jpg',
                  deeplink_url: '#'
                }
              ]
            },
            {
              city: 'Ayutthaya',
              check_in: '2025-10-04',
              check_out: '2025-10-06',
              nights: 2,
              hotels: [
                {
                  city: 'Ayutthaya',
                  name: 'Sala Ayutthaya',
                  area: 'Riverside',
                  price_tier: 'premium',
                  notes: 'Boutique hotel with river views.',
                  image_url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/%E0%B8%AA%E0%B8%96%E0%B8%B2%E0%B8%99%E0%B8%B5%E0%B8%AD%E0%B8%A2%E0%B8%B8%E0%B8%98%E0%B8%A2%E0%B8%B2.jpg/960px-%E0%B8%AA%E0%B8%96%E0%B8%B2%E0%B8%99%E0%B8%B5%E0%B8%AD%E0%B8%A2%E0%B8%B8%E0%B8%98%E0%B8%A2%E0%B8%B2.jpg',
                  deeplink_url: '#'
                },
                {
                  city: 'Ayutthaya',
                  name: 'Baan Tye Wang Guesthouse',
                  area: 'Old City',
                  price_tier: 'budget',
                  notes: 'Traditional guesthouse in historic area.',
                  image_url: null,
                  deeplink_url: '#'
                }
              ]
            },
            {
              city: 'Sukhothai',
              check_in: '2025-10-06',
              check_out: '2025-10-09',
              nights: 3,
              hotels: [
                {
                  city: 'Sukhothai',
                  name: 'Sukhothai Heritage Resort',
                  area: 'Historical Park',
                  price_tier: 'premium',
                  notes: 'Luxury resort near UNESCO World Heritage site.',
                  image_url: null,
                  deeplink_url: '#'
                },
                {
                  city: 'Sukhothai',
                  name: 'Sawasdee Sukhothai Resort',
                  area: 'New Sukhothai',
                  price_tier: 'mid',
                  notes: 'Comfortable resort with traditional architecture.',
                  image_url: null,
                  deeplink_url: '#'
                },
                {
                  city: 'Sukhothai',
                  name: 'Thai Thai Sukhothai Guesthouse',
                  area: 'Old City',
                  price_tier: 'budget',
                  notes: 'Budget-friendly guesthouse with local charm.',
                  image_url: null,
                  deeplink_url: '#'
                }
              ]
            },
            {
              city: 'Chiang Mai',
              check_in: '2025-10-09',
              check_out: '2025-10-12',
              nights: 3,
              hotels: [
                {
                  city: 'Chiang Mai',
                  name: 'U Nimman Chiang Mai',
                  area: 'Nimman',
                  price_tier: 'premium',
                  notes: 'In the trendy Nimman area.',
                  image_url: null,
                  deeplink_url: '#'
                },
                {
                  city: 'Chiang Mai',
                  name: 'De Naga Hotel Chiang Mai',
                  area: 'Old City',
                  price_tier: 'mid',
                  notes: 'Traditional hotel with local charm.',
                  image_url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/0020-%E0%B8%A7%E0%B8%B1%E0%B8%94%E0%B8%9E%E0%B8%A3%E0%B8%B0%E0%B8%AA%E0%B8%B4%E0%B8%87%E0%B8%AB%E0%B9%8C%E0%B8%A7%E0%B8%A3%E0%B8%A1%E0%B8%AB%E0%B8%B2%E0%B8%A7%E0%B8%B4%E0%B8%AB%E0%B8%B2%E0%B8%A3.jpg/960px-0020-%E0%B8%A7%E0%B8%B1%E0%B8%94%E0%B8%9E%E0%B8%A3%E0%B8%B0%E0%B8%AA%E0%B8%B4%E0%B8%87%E0%B8%AB%E0%B9%8C%E0%B8%A7%E0%B8%A3%E0%B8%A1%E0%B8%AB%E0%B8%B2%E0%B8%A7%E0%B8%B4%E0%B8%AB%E0%B8%B2%E0%B8%A3.jpg',
                  deeplink_url: '#'
                },
                {
                  city: 'Chiang Mai',
                  name: 'Green Tiger Vegetarian House',
                  area: 'Old City',
                  price_tier: 'budget',
                  notes: 'Eco-friendly and budget-friendly.',
                  image_url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/Soy-whey-protein-diet.jpg/960px-Soy-whey-protein-diet.jpg',
                  deeplink_url: '#'
                }
              ]
            },
            {
              city: 'Phuket',
              check_in: '2025-10-12',
              check_out: '2025-10-15',
              nights: 3,
              hotels: [
                {
                  city: 'Phuket',
                  name: 'The Marina Phuket Hotel',
                  area: 'Patong Beach',
                  price_tier: 'premium',
                  notes: 'Beachfront luxury with vibrant nightlife.',
                  image_url: null,
                  deeplink_url: '#'
                },
                {
                  city: 'Phuket',
                  name: 'Amari Phuket',
                  area: 'Patong Beach',
                  price_tier: 'mid',
                  notes: 'Beachfront with good nightlife.',
                  image_url: 'https://upload.wikimedia.org/wikipedia/commons/5/5d/Amari_New_Logo.png',
                  deeplink_url: '#'
                },
                {
                  city: 'Phuket',
                  name: 'The Shore at Katathani',
                  area: 'Katathani Beach',
                  price_tier: 'premium',
                  notes: 'Private villas with sea views.',
                  image_url: null,
                  deeplink_url: '#'
                }
              ]
            }
          ]
        } };
      }

      if (path.endsWith(`/api/travels/${travelId}/transport-plan`) && method === 'GET') {
        return { status: 200, body: {
          travel_id: travelId,
          transport_plan: {
            segments: [
              { from: 'Bangkok', to: 'Ayutthaya', method: 'train', distance_km: 80, duration_h: 1.5, estimated_cost: 8 },
              { from: 'Ayutthaya', to: 'Sukhothai', method: 'intercity_bus', distance_km: 350, duration_h: 4, estimated_cost: 15 },
              { from: 'Sukhothai', to: 'Chiang Mai', method: 'intercity_bus', distance_km: 300, duration_h: 5, estimated_cost: 20 },
              { from: 'Chiang Mai', to: 'Phuket', method: 'flight', distance_km: 1200, duration_h: 2, estimated_cost: 120 }
            ],
            totals: {
              segments: 4,
              total_distance_km: 1930,
              total_duration_h: 12.5,
              total_cost: 163
            }
          }
        } };
      }

      return null;
    }

    function routeFetch(url, options = {}) {
      try {
        const u = new URL(url, window.location.origin);
        const path = u.pathname;
        const method = (options.method || 'GET').toUpperCase();
        const mock = buildMockBodyFor(path, method, u.searchParams, options.body);
        if (mock) return jsonResponse(mock.body, { status: mock.status });

        // Fallback to real fetch for anything else
        return originalFetch(url, options);
      } catch (e) {
        return jsonResponse({ error: 'mock_fetch_error', detail: String(e) }, { status: 500 });
      }
    }

    class MockWebSocket {
      constructor(url) {
        this.url = url;
        this.readyState = 0; // CONNECTING
        this.onopen = null;
        this.onmessage = null;
        this.onclose = null;
        this.onerror = null;

        // Simulate async open
        setTimeout(() => {
          this.readyState = 1; // OPEN
          this.onopen && this.onopen({});
        }, 50);
      }

      send(text) {
        try {
          const parsed = JSON.parse(text);
          // Respond with a demo assistant message
          if (parsed && parsed.type === 'message') {
            const cid = (parsed.data && parsed.data.correlation_id) || `cid-${Date.now()}`;
            const demo = {
              type: 'message',
              data: {
                id: `demo-${Date.now()}`,
                content: '[DEMO] Itinerario sugerido: Bangkok (3d), Chiang Mai (2d), Phuket (2d). ¿Te gusta este plan?',
                is_user: false,
                intention: 'demo_reply',
                classification: { type: 'demo', confidence: 1.0, reason: 'MOCK', extracted_country: 'thailand' },
                correlation_id: cid,
                timestamp: new Date().toISOString(),
                travel_id: demoTravelId,
                user_id: 'assistant',
              },
            };
            setTimeout(() => {
              this.onmessage && this.onmessage({ data: JSON.stringify(demo) });
            }, 300);
          }
        } catch (e) {
          this.onerror && this.onerror(e);
        }
      }

      close(code) {
        this.readyState = 3; // CLOSED
        this.onclose && this.onclose({ code: code || 1000 });
      }
    }

    // Install mocks
    window.fetch = routeFetch;
    window.WebSocket = MockWebSocket;
    try {
      // Pre-seed token/user so the UI bypasses auth checks naturally
      if (!localStorage.getItem('token')) localStorage.setItem('token', 'demo-token');
      if (!localStorage.getItem('userId')) localStorage.setItem('userId', 'demo-user-1');
    } catch (e) {}
    // Hook XHR for Axios
    if (XHROpen && XHRSend) {
      XMLHttpRequest.prototype.open = function(method, url) {
        this.__mockMethod = String(method || 'GET').toUpperCase();
        this.__mockUrl = url;
        return XHROpen.apply(this, arguments);
      };
      XMLHttpRequest.prototype.send = function(body) {
        try {
          const u = new URL(this.__mockUrl, window.location.origin);
          const path = u.pathname;
          const method = this.__mockMethod || 'GET';
          const mock = buildMockBodyFor(path, method, u.searchParams, body);
          if (mock) {
            const self = this;
            setTimeout(function() {
              self.readyState = 4;
              self.status = mock.status;
              self.responseText = JSON.stringify(mock.body);
              self.response = self.responseText;
              if (typeof self.onreadystatechange === 'function') self.onreadystatechange();
              if (typeof self.onload === 'function') self.onload();
            }, 50);
            return;
          }
        } catch (e) {
          // fallthrough
        }
        return XHRSend.apply(this, arguments);
      };
    }
    console.info('[DEMO MOCK] Frontend mocks enabled (REACT_APP_MOCK=true)');
  } catch (e) {
    // Fail-safe: if mock install fails, keep the app running with originals
    console.warn('[DEMO MOCK] Failed to initialize mocks:', e);
  }
})();



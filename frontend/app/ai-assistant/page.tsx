"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Bot, Sparkles } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { ChatMessages } from "@/components/ai/chat-messages";
import { ChatInput } from "@/components/ai/chat-input";
import { ConversationSidebar } from "@/components/ai/conversation-sidebar";
import { SuggestedPrompts } from "@/components/ai/suggested-prompts";
import type { ChatMessage, Source } from "@/types";
import { generateId } from "@/lib/utils";

const WELCOME_MESSAGE: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content:
    "Hello! I'm **CropPilot AI** — your intelligent agricultural assistant. 🌾\n\nI can help you with:\n\n- **Crop management** — sowing, irrigation, fertilization schedules\n- **Disease detection** — identify and treat crop diseases\n- **Market analysis** — real-time mandi prices and trends\n- **Government schemes** — find schemes you're eligible for\n- **Weather insights** — forecast and its impact on your crops\n\nWhat would you like to know about your farm today?",
  timestamp: new Date().toISOString(),
};

const MOCK_RESPONSES: Record<string, string> = {
  default: `Great question! Let me share some insights based on current agricultural data.

## Key Recommendations

1. **Soil Preparation** — Ensure proper soil testing before sowing. The ideal pH for most crops is between 6.0 and 7.5.

2. **Nutrient Management** — Apply recommended doses of NPK fertilizers based on soil test results.

3. **Water Management** — Implement drip irrigation for better water efficiency. It can save up to 40% water compared to flood irrigation.

4. **Pest Control** — Regular monitoring is essential. Use integrated pest management (IPM) techniques.

## Quick Tips

- Always source certified seeds from reputable dealers
- Maintain proper crop rotation to prevent soil-borne diseases
- Monitor weather forecasts regularly for timely farm operations

Need more specific advice? Feel free to ask about any particular crop or issue!`,

  wheat: `Here's a comprehensive guide for **wheat cultivation in Punjab**:

## Sowing Time
| Season | Sowing Period | Harvest |
|--------|--------------|---------|
| Rabi | Oct-Nov | Apr-May |

## Recommended Varieties
- **HD 2967** — High yield, rust resistant
- **HD 3086** — Excellent for Punjab conditions
- **PBW 723** — Biofortified, zinc-rich

## Fertilizer Schedule (per hectare)
| Nutrient | Basal Dose | Top Dressing |
|----------|-----------|--------------|
| Nitrogen | 60 kg | 60 kg (at CRI stage) |
| Phosphorus | 50 kg | — |
| Potash | 40 kg | — |

## Irrigation
- **Critical stages:** Crown root initiation (CRI), tillering, flowering, grain filling
- Total of 5-6 irrigations recommended for optimal yield

- **Average yield:** 45-50 quintals/hectare
- **MSP (2025):** ₹2,425/quintal

> Pro tip: Apply first irrigation at CRI stage (21-25 days after sowing) for optimal tillering!`,

  disease: `## Leaf Blight in Tomatoes — Identification & Treatment

### Symptoms
| Symptom | Description |
|---------|------------|
| **Leaf spots** | Dark brown to black, irregular spots with yellow halos |
| **Stem lesions** | Elongated dark lesions on stems |
| **Fruit rot** | Sunken, dark, leathery spots on fruits |
| **Defoliation** | Severe leaf drop in advanced stages |

### Management Strategy

#### 1. Cultural Control 🛡️
- Remove and destroy infected plant debris
- Practice crop rotation (avoid solanaceous crops for 2-3 years)
- Ensure proper spacing for air circulation
- Avoid overhead irrigation

#### 2. Chemical Control 🧪
| Fungicide | Dosage | Interval |
|-----------|--------|----------|
| Mancozeb (75% WP) | 2.5 g/L | 7-10 days |
| Chlorothalonil | 2 g/L | 10-14 days |
| Copper Oxychloride | 3 g/L | 7-10 days |

#### 3. Biological Control 🌿
- Apply *Trichoderma viride* (5 g/L) as soil treatment
- Use *Pseudomonas fluorescens* for seed treatment
- Neem oil (3%) spray as preventive measure

### Prevention Tips ✅
- Use disease-free certified seeds
- Treat seeds with hot water (52°C for 30 min)
- Apply mulching to reduce soil splash

Need help identifying a specific disease? Upload a photo of the affected plant and I'll help diagnose it!`,

  market: `## Current Market Prices in Punjab

### Today's Mandi Rates 🏪

| Commodity | Variety | Modal Price (₹/quintal) | Change |
|-----------|---------|------------------------|--------|
| **Wheat** | Sharbati | 2,625 | ▲ +2.3% |
| **Rice** | Pusa 1121 | 3,450 | ▲ +1.8% |
| **Maize** | Hybrid | 1,875 | ▼ -0.6% |
| **Cotton** | Bt | 5,620 | ▲ +4.2% |
| **Potato** | Jyoti | 1,280 | ▼ -1.5% |
| **Onion** | Red | 1,850 | ▲ +3.1% |

### Market Insights 📊

**Top Gainers:**
- **Cotton** (+4.2%) — Strong export demand driving prices up
- **Onion** (+3.1%) — Lower arrival volumes due to off-season

**Top Losers:**
- **Potato** (-1.5%) — Increased supply from cold storage releases
- **Maize** (-0.6%) — Steady arrivals from Kharif harvest

### Recommendations 💡
- **Hold** wheat stock until December for better prices
- **Sell** cotton now as prices are at seasonal highs
- Consider **forward contracts** for wheat at current MSP levels

> *Prices sourced from AGMARKNET. Last updated: Today 10:30 AM*`,

  schemes: `## Government Schemes for Small Farmers 🇮🇳

Based on your profile, here are the schemes you're **eligible** for:

### 1. PM-KISAN Samman Nidhi ✅
| Detail | Info |
|--------|------|
| **Benefit** | ₹6,000/year in 3 equal installments |
| **Eligibility** | All small & marginal farmers |
| **Status** | **You can apply** — Direct benefit transfer to bank |
| **Documents** | Aadhaar, land records, bank account |

### 2. Pradhan Mantri Fasal Bima Yojana ✅
| Detail | Info |
|--------|------|
| **Coverage** | Crop loss due to natural calamities |
| **Premium** | 2% (Kharif) / 1.5% (Rabi) — balance subsidized |
| **Status** | Enroll before sowing deadline |

### 3. Soil Health Card Scheme ✅
| Detail | Info |
|--------|------|
| **Benefit** | Free soil testing & fertilizer recommendations |
| **Valid for** | 2 years |
| **Apply at** | Nearest agriculture office or online |

### 4. Kisan Credit Card (KCC) ✅
| Detail | Info |
|--------|------|
| **Loan limit** | Up to ₹3 lakh at 4% interest (prompt repayment) |
| **Purpose** | Crop cultivation, maintenance, marketing |

### How to Apply 📝
1. Visit [PM-KISAN portal](https://pmkisan.gov.in) or nearest CSC
2. Have Aadhaar and land records ready
3. Submit application online — it takes **15 minutes**

Would you like me to help you fill out any of these applications?`,

  weather: `## Weather Impact on Kharif Crops 🌤️

### Current Conditions
| Parameter | Value | Status |
|-----------|-------|--------|
| Temperature | 32°C | Normal |
| Humidity | 68% | Moderate |
| Rainfall | 12 mm (last 24h) | Adequate |
| Wind | 12 km/h | Gentle breeze |

### 7-Day Forecast

| Day | Temp | Rain Probability | Advisory |
|-----|------|-----------------|----------|
| Today | 30-34°C | 30% | Continue irrigation schedule |
| Tomorrow | 28-32°C | 60% | Postpone pesticide spray |
| Day 3 | 26-30°C | 80% | **Heavy rain alert** — Check drainage |
| Day 4 | 27-31°C | 40% | Resume normal operations |
| Day 5 | 29-33°C | 20% | Ideal for fertilizer application |
| Day 6 | 30-34°C | 10% | Good for harvesting |
| Day 7 | 31-35°C | 15% | Monitor for pest activity |

### Crop-Specific Recommendations

- **Rice (Kharif):** Ensure adequate water in standing crop. The forecast rain will help reduce irrigation needs.
- **Cotton:** Watch for bollworm activity in high humidity. Spray recommended after rains subside.
- **Maize:** Good time for top dressing of nitrogen before the expected heavy rain.

### Precautions ⚠️
1. Clear drainage channels before Day 3
2. Store harvested produce in covered area
3. Delay any pesticide/fertilizer application until after rain
4. Use plastic mulching to protect young seedlings`,

  rotation: `## Crop Rotation Plan for Your Farm 🌾

Based on your soil type and region, here's an **optimal 3-year rotation cycle**:

### Year 1: Soil Building
| Season | Crop | Benefit |
|--------|------|---------|
| **Kharif** | Green Manure (Dhaincha/Sesbania) | Fixes nitrogen, improves organic matter |
| **Rabi** | Wheat | Good residue for next crop |

### Year 2: Cash Crops
| Season | Crop | Benefit |
|--------|------|---------|
| **Kharif** | Cotton | Deep root system breaks hardpan |
| **Rabi** | Chickpea (Chana) | Legume fixes atmospheric nitrogen |

### Year 3: Cereal Rotation
| Season | Crop | Benefit |
|--------|------|---------|
| **Kharif** | Rice/Paddy | Utilizes residual nutrients |
| **Rabi** | Mustard | Biofumigation controls soil pests |

### Soil Management Tips 🧑‍🌾

| Practice | Timing | Benefit |
|----------|--------|---------|
| **Soil testing** | Before each Kharif | Prevents over-fertilization |
| **Compost application** | 5 tonnes/ha annually | Improves soil structure |
| **Lime/Gypsum** | As per soil test | Corrects pH/sodicity |
| **Deep ploughing** | Once in 3 years | Breaks hardpan, improves drainage |

### Expected Benefits 📈
- **20-30%** increase in overall productivity
- **15-20%** reduction in fertilizer costs
- **40%** reduction in pest incidence
- Improved soil health and water retention

Would you like me to create a customized plan for your specific farm size and location?`,
};

function getMockResponse(message: string): string {
  const lower = message.toLowerCase();
  if (lower.includes("wheat") && (lower.includes("punjab") || lower.includes("cultivat"))) return MOCK_RESPONSES.wheat;
  if (lower.includes("blight") || lower.includes("disease") || lower.includes("pest") || lower.includes("fungus") || lower.includes("mildew")) return MOCK_RESPONSES.disease;
  if (lower.includes("market") || lower.includes("price") || lower.includes("mandi") || lower.includes("sell") || lower.includes("rate")) return MOCK_RESPONSES.market;
  if (lower.includes("scheme") || lower.includes("government") || lower.includes("subsidy") || lower.includes("pm") || lower.includes("kisan")) return MOCK_RESPONSES.schemes;
  if (lower.includes("weather") || lower.includes("rain") || lower.includes("forecast") || lower.includes("temperature")) return MOCK_RESPONSES.weather;
  if (lower.includes("rotation") || lower.includes("soil") || lower.includes("planning") || lower.includes("crop rotation")) return MOCK_RESPONSES.rotation;
  return MOCK_RESPONSES.default;
}

function extractSources(content: string): Source[] {
  const sources: Source[] = [];
  const tableMatch = content.match(/\|.*\|/g);
  if (tableMatch && tableMatch.length > 1) {
    sources.push({
      title: "Agricultural Data Reference",
      content: "Government published agricultural statistics and recommendations",
      score: 0.92,
    });
  }
  if (content.includes("MSP") || content.includes("₹")) {
    sources.push({
      title: "Mandi Price Report",
      content: "AGMARKNET and e-NAM market intelligence data",
      score: 0.88,
    });
  }
  if (content.includes("PM-KISAN") || content.includes("Fasal Bima") || content.includes("Kisan Credit Card")) {
    sources.push({
      title: "Government Schemes Database",
      content: "Official Indian government agricultural scheme documentation",
      score: 0.95,
    });
  }
  if (sources.length === 0) {
    sources.push({
      title: "CropPilot Knowledge Base",
      content: "AI-generated agricultural advisory based on best practices",
      score: 0.85,
    });
  }
  return sources;
}

interface Conversation {
  id: string;
  title: string;
  preview: string;
  date: string;
  messageCount: number;
}

export default function AiAssistantPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([
    {
      id: "conv-default",
      title: "Welcome to CropPilot",
      preview: "Hello! I'm CropPilot AI...",
      date: new Date().toISOString(),
      messageCount: 1,
    },
  ]);
  const [activeConversation, setActiveConversation] = useState<string>("conv-default");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const abortRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        setSidebarCollapsed(true);
      }
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const createNewConversation = useCallback(() => {
    const id = generateId();
    const conv: Conversation = {
      id,
      title: "New Chat",
      preview: "Start a conversation...",
      date: new Date().toISOString(),
      messageCount: 0,
    };
    setConversations((prev) => [conv, ...prev]);
    setActiveConversation(id);
    setMessages([WELCOME_MESSAGE]);
  }, []);

  const handleSend = useCallback(
    async (content: string) => {
      const userMessage: ChatMessage = {
        id: generateId(),
        role: "user",
        content,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsGenerating(true);

      setConversations((prev) =>
        prev.map((c) =>
          c.id === activeConversation
            ? {
                ...c,
                title: c.messageCount === 0 ? content.slice(0, 50) : c.title,
                preview: content.slice(0, 60),
                date: new Date().toISOString(),
                messageCount: c.messageCount + 1,
              }
            : c
        )
      );

      const fullResponse = getMockResponse(content);
      const sources = extractSources(fullResponse);
      const words = fullResponse.split(" ");
      let accumulated = "";
      let wordIndex = 0;
      let cancelled = false;

      abortRef.current = () => {
        cancelled = true;
      };

      const assistantId = generateId();
      const assistantMessage: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        timestamp: new Date().toISOString(),
        sources,
      };
      setMessages((prev) => [...prev, assistantMessage]);

      const typeNextChunk = () => {
        if (cancelled) {
          setIsGenerating(false);
          return;
        }

        const chunkSize = Math.floor(Math.random() * 3) + 1;
        const chunk = words.slice(wordIndex, wordIndex + chunkSize).join(" ");
        accumulated += (accumulated ? " " : "") + chunk;
        wordIndex += chunkSize;

        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: accumulated } : m
          )
        );

        if (wordIndex < words.length) {
          const delay = 30 + Math.random() * 50;
          setTimeout(typeNextChunk, delay);
        } else {
          setIsGenerating(false);
          abortRef.current = null;
          setConversations((prev) =>
            prev.map((c) =>
              c.id === activeConversation
                ? { ...c, messageCount: c.messageCount + 1 }
                : c
            )
          );
        }
      };

      setTimeout(typeNextChunk, 300);
    },
    [activeConversation]
  );

  const handleSelectConversation = useCallback(
    (id: string) => {
      setActiveConversation(id);
      setMobileSidebarOpen(false);
    },
    []
  );

  const handleDeleteConversation = useCallback((id: string) => {
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (id === activeConversation) {
      setMessages([WELCOME_MESSAGE]);
      setActiveConversation("conv-default");
    }
  }, [activeConversation]);

  const handlePromptSelect = useCallback(
    (prompt: string) => {
      handleSend(prompt);
    },
    [handleSend]
  );

  return (
    <DashboardLayout>
      <div className="flex h-[calc(100vh-4rem)] -m-4 lg:-m-6">
        <div className="hidden lg:flex">
          <ConversationSidebar
            conversations={conversations}
            activeId={activeConversation}
            onSelect={handleSelectConversation}
            onNew={createNewConversation}
            onDelete={handleDeleteConversation}
            isCollapsed={sidebarCollapsed}
            onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          />
        </div>

        <AnimatePresence>
          {mobileSidebarOpen && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setMobileSidebarOpen(false)}
                className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
              />
              <motion.div
                initial={{ x: "-100%" }}
                animate={{ x: 0 }}
                exit={{ x: "-100%" }}
                transition={{ type: "spring", damping: 30, stiffness: 300 }}
                className="fixed inset-y-0 left-0 z-50 w-72 lg:hidden"
              >
                <ConversationSidebar
                  conversations={conversations}
                  activeId={activeConversation}
                  onSelect={handleSelectConversation}
                  onNew={createNewConversation}
                  onDelete={handleDeleteConversation}
                  isCollapsed={false}
                  onToggleCollapse={() => setMobileSidebarOpen(false)}
                />
              </motion.div>
            </>
          )}
        </AnimatePresence>

        <div className="flex flex-1 flex-col min-w-0 bg-background">
          <div className="flex items-center justify-between border-b border-border px-4 py-2 lg:hidden">
            <button
              onClick={() => setMobileSidebarOpen(true)}
              className="flex items-center gap-2 text-sm font-medium text-foreground"
            >
              <MessageSquare className="h-4 w-4" />
              Conversations
            </button>
            <div className="flex items-center gap-2">
              <button
                onClick={createNewConversation}
                className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground"
              >
                <Sparkles className="h-3.5 w-3.5" />
                New Chat
              </button>
            </div>
          </div>

          {messages.length === 1 && messages[0].id === "welcome" && !isGenerating ? (
            <div className="flex-1 flex flex-col items-center justify-center overflow-y-auto px-4">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="mb-8 text-center"
              >
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
                  <Bot className="h-8 w-8 text-primary" />
                </div>
                <h1 className="text-2xl font-bold text-foreground">
                  CropPilot AI Assistant
                </h1>
                <p className="mt-2 text-sm text-muted-foreground max-w-md mx-auto">
                  Your intelligent farming companion — ask anything about agriculture
                </p>
              </motion.div>
              <SuggestedPrompts onSelect={handlePromptSelect} />
            </div>
          ) : (
            <ChatMessages messages={messages} isGenerating={isGenerating} />
          )}

          <ChatInput
            onSend={handleSend}
            disabled={isGenerating}
            suggestedPrompts={
              messages.length <= 1
                ? [
                    "Best practices for wheat cultivation",
                    "Identify tomato leaf blight",
                    "Current mandi prices",
                    "Government schemes for farmers",
                  ]
                : undefined
            }
          />
        </div>
      </div>
    </DashboardLayout>
  );
}

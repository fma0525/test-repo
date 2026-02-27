import { Story, StoryStyle } from "./types";

// Mock 故事資料 — 在沒有 API Key 時使用
const MOCK_STORIES_DB: Story[] = [
  {
    id: "mock-1",
    title: "小熊的星空冒險",
    keywords: ["小熊", "太空", "星星"],
    style: "adventure",
    full_text: `從前從前，在一座高高的山頂上，住著一隻好奇的小熊。

每天晚上，小熊都會抬頭看著滿天的星星，心裡想：「星星的家在哪裡呢？」

有一天晚上，一顆特別亮的星星突然「咻——」地飛了下來！

「嗨！小熊！」星星眨眨眼睛說，「你想不想到天上來玩？」

小熊高興得跳了起來：「真的可以嗎？太棒了！」

星星變成一艘金色的小船，帶著小熊飛上了天空。

他們經過了白白的雲朵，雲朵軟軟的像棉花糖。
他們經過了彎彎的月亮，月亮笑著跟他們揮手。
他們還看到了好多好多星星，每顆星星都在唱歌。

「哇！原來星星都住在一起，就像一個大家庭！」小熊說。

星星笑著說：「對呀！我們每天晚上都會在天上唱歌跳舞，陪小朋友們入睡呢。」

小熊開心地在星星之間飛來飛去，還交了好多星星朋友。

最後，星星把小熊送回了山頂。

「謝謝你帶我去冒險！」小熊揮揮手。

「明天晚上，記得抬頭看天空喔，我會特別亮地跟你打招呼！」星星說完，就飛回天上了。

從那天起，小熊每天晚上都會對著天空的星星微笑，因為他知道，那些星星都是他的朋友。`,
    cover_image_url: "",
    audio_url: "",
    duration: 180,
    created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
  },
  {
    id: "mock-2",
    title: "海底的生日派對",
    keywords: ["海洋", "生日", "魚"],
    style: "funny",
    full_text: `在深深的海底，住著一隻叫做泡泡的小丑魚。

今天是泡泡的生日，他開心地游來游去：「今天是我的生日！我要辦一場超級大派對！」

泡泡去找章魚阿八幫忙。

「阿八，你可以用你的八隻手幫我做蛋糕嗎？」

章魚阿八拍拍胸口說：「沒問題！看我的！」

結果阿八八隻手同時攪拌，把海水都攪成了大漩渦！

「噗通！噗通！」好多小魚被捲得團團轉。

「哎呀呀！」泡泡笑得前仰後合。

大海龜爺爺慢慢游過來：「蛋糕在哪裡？我聞到好香好香的味道！」

「海龜爺爺，蛋糕還沒做好呢！你聞到的是海草的味道啦！」

「什麼？！」海龜爺爺張大嘴巴，「海草也很好吃嘛！咔嚓咔嚓！」

他一口就把旁邊的海草吃光光了。

大家一起哈哈大笑！

最後，阿八終於做好了一個歪歪扭扭的海底蛋糕，上面插著會發光的小水母當蠟燭。

「一、二、三，吹蠟燭！」

泡泡深吸一口氣，「呼——」

他吹出了世界上最大的一個泡泡！

泡泡裡面裝著他的願望，慢慢飄向了海面。

「我的願望是——每天都能和好朋友在一起！」

所有的海洋朋友們一起歡呼：「生日快樂！泡泡！」

這是海底最棒最熱鬧的一場生日派對！`,
    cover_image_url: "",
    audio_url: "",
    duration: 210,
    created_at: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: "mock-3",
    title: "月亮上的小兔子",
    keywords: ["月亮", "兔子", "友誼"],
    style: "goodnight",
    full_text: `月亮升起來了，圓圓的、亮亮的。

在月亮上面，住著一隻軟軟的小白兔，名字叫做月月。

月月每天晚上都會坐在月亮邊邊，輕輕地看著地球上的小朋友們。

「那個小朋友在刷牙了呢。」月月小聲地說。
「那個小朋友在聽媽媽說故事了呢。」

月月最喜歡做的事情，就是幫小朋友們蓋上星星做的被子。

她會輕輕地、輕輕地，把一顆一顆小星星撒下去。

星星落在小朋友的窗台上，變成了柔柔的光。

「這樣，小朋友就不會怕黑黑了。」月月微笑著說。

今天晚上，月月發現一個小朋友還沒有睡著。

小朋友躺在床上，眼睛大大的，看著窗外的月亮。

「月亮好漂亮呀⋯⋯」小朋友輕輕說。

月月聽到了，她開心地搖搖長長的耳朵。

然後，她唱了一首很輕很輕的歌：

「小星星，亮晶晶，陪你睡到天亮亮。
小月亮，圓又圓，在你夢裡笑瞇瞇。」

小朋友聽著聽著，眼皮越來越重⋯⋯越來越重⋯⋯

「晚安，小朋友。」月月輕輕地說。

「晚安，月亮上的小兔子⋯⋯」小朋友在夢裡回答。

月月笑了，繼續守著這個美麗的夜晚，直到明天。

晚安。`,
    cover_image_url: "",
    audio_url: "",
    duration: 165,
    created_at: new Date().toISOString(),
  },
];

// Mock 故事生成模板
const MOCK_GENERATED_STORIES: Record<string, { title: string; full_text: string }> = {
  default: {
    title: "森林裡的小冒險",
    full_text: `在一片綠油油的森林裡，住著一隻愛唱歌的小鳥和一隻愛跳舞的小松鼠。

每天早上，小鳥都會站在最高的樹枝上唱歌：「啾啾啾！今天又是美好的一天！」

小松鼠聽到歌聲，就會在樹幹上轉圈圈跳舞：「我也覺得！今天一定會發生有趣的事！」

有一天，他們發現了一條從來沒走過的小路。

「你敢走嗎？」小鳥問。

小松鼠挺起胸膛：「當然敢！只要我們一起走！」

他們沿著小路走啊走，經過了一片會發光的蘑菇田。
蘑菇們一閃一閃的，像地上的小星星。

「哇！好漂亮呀！」兩個好朋友一起說。

小路的盡頭，是一棵超級超級大的老橡樹。

老橡樹慢慢張開眼睛：「歡迎你們，小朋友們。我在這裡等了好久好久。」

「等我們？為什麼呢？」小鳥好奇地問。

「因為只有勇敢又善良的朋友，才能找到這條路。」老橡樹笑著說，「送你們一個禮物吧。」

老橡樹搖了搖枝葉，落下了兩顆金色的橡實。

「把它種下去，明年春天就會長出一棵友誼之樹。」

小鳥和小松鼠開心地收下了禮物。

「謝謝老橡樹爺爺！」

他們帶著橡實回到了家，一起把它種在了森林最漂亮的地方。

從那天起，他們知道了一個秘密：只要有勇氣和好朋友在身邊，就能發現世界上最美好的事情。`,
  },
};

// 內存存儲（Mock 模式下替代資料庫）
let mockStories: Story[] = [...MOCK_STORIES_DB];

export function getMockStories(): Story[] {
  return mockStories.sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
}

export function getMockStory(id: string): Story | undefined {
  return mockStories.find((s) => s.id === id);
}

export function addMockStory(keywords: string[], style: StoryStyle): Story {
  const template = MOCK_GENERATED_STORIES.default;
  const newStory: Story = {
    id: `mock-${Date.now()}`,
    title: `${keywords.join("與")}的故事`,
    keywords,
    style,
    full_text: template.full_text,
    cover_image_url: "",
    audio_url: "",
    duration: 150 + Math.floor(Math.random() * 120),
    created_at: new Date().toISOString(),
  };
  mockStories.unshift(newStory);
  return newStory;
}

export function isMockMode(): boolean {
  return process.env.USE_MOCK === "true" || !process.env.ANTHROPIC_API_KEY;
}

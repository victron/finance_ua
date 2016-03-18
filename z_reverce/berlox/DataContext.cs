// Decompiled with JetBrains decompiler
// Type: BXFinanceDashboard.DataContext
// Assembly: BXFinanceDashboard, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null
// MVID: 041FC1B4-8068-406E-B73C-60093F7A721F
// Assembly location: C:\Program Files\WindowsApps\30539Berlox.UA_1.3.0.2_neutral__ewsz346h4esd0\BXFinanceDashboard.exe

using BXFinanceCore;
using Compression;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices.WindowsRuntime;
using System.Text;
using System.Threading.Tasks;
using Windows.Networking.BackgroundTransfer;
using Windows.Storage;
using Windows.Storage.Streams;
using Windows.System.Profile;
using Windows.Web.Http;
using Windows.Web.Http.Filters;

namespace BXFinanceDashboard
{
  public class DataContext
  {
    public const string DEFAULT_CITY = "Киев";
    public const bool USE_COMPRESSION = true;
    public const string API_URL = "http://berlox.com/finance/api";
    public const string LIVE_DATA_URL = "http://berlox.com/finance/data.bin";
    public const string LIVE_DATAZ_URL = "http://berlox.com/finance/dataz.bin";
    public const string LIVE_LIST_URL = "http://berlox.com/finance/list.bin";
    public const string LIVE_LISTZ_URL = "http://berlox.com/finance/listz.bin";
    public const string LOCAL_DATA_FILENAME = "data.json";
    public const string LOCAL_MYDEALS_FILENAME = "mydeals.json";
    public const string LOCAL_CITIES_FILENAME = "cities.txt";

    public async Task<FinanceInfo> GetCachedFinanceDataAsync()
    {
      string json = await this.ReadLocalFileAsync("data.json");
      FinanceInfo result = await Task.Factory.StartNew<FinanceInfo>((Func<FinanceInfo>) (() => JsonConvert.DeserializeObject<FinanceInfo>(json)));
      return result;
    }

    public async Task<FinanceInfo> GetLiveFinanceDataAsync()
    {
      Uri uri = new Uri("http://berlox.com/finance/dataz.bin");
      string json = string.Empty;
      byte[] buff = await this.GetWebData(uri, false);
      if (buff != null && buff.Length > 0)
      {
        byte[] key = DataKey.GetCurrentKey();
        json = await Task.Factory.StartNew<string>((Func<string>) (() => Compression.DecompressToString(new SimpleAES(key).Decrypt(buff))));
      }
      FinanceInfo result = await Task.Factory.StartNew<FinanceInfo>((Func<FinanceInfo>) (() => JsonConvert.DeserializeObject<FinanceInfo>(json)));
      try
      {
        await this.WriteLocalFileAsync("data.json", json);
      }
      catch
      {
      }
      return result;
    }

    public async Task<MarketListing> GetLiveListingDataAsync()
    {
      Uri uri = new Uri("http://berlox.com/finance/listz.bin");
      string json = string.Empty;
      byte[] buff = await this.GetWebData(uri, true);
      if (buff != null && buff.Length > 0)
      {
        byte[] key = DataKey.GetCurrentKey();
        json = await Task.Factory.StartNew<string>((Func<string>) (() => Compression.DecompressToString(new SimpleAES(key).Decrypt(buff))));
      }
      MarketListing result = await Task.Factory.StartNew<MarketListing>((Func<MarketListing>) (() => JsonConvert.DeserializeObject<MarketListing>(json)));
      await this.SaveCityListAsync(result);
      return result;
    }

    public static void RegisterPrefetchUrls()
    {
      try
      {
        if (Enumerable.Any<Uri>((IEnumerable<Uri>) ContentPrefetcher.get_ContentUris(), (Func<Uri, bool>) (u => u.AbsoluteUri == "http://berlox.com/finance/data.bin")))
          return;
        ContentPrefetcher.get_ContentUris().Clear();
        ContentPrefetcher.get_ContentUris().Add(new Uri("http://berlox.com/finance/data.bin"));
      }
      catch
      {
      }
    }

    private async Task<byte[]> GetWebData(Uri uri, bool bypassCahce)
    {
      HttpBaseProtocolFilter filter = new HttpBaseProtocolFilter();
      if (bypassCahce)
        filter.get_CacheControl().put_ReadBehavior((HttpCacheReadBehavior) 1);
      HttpClient client = new HttpClient((IHttpFilter) filter);
      IBuffer ibuff = await client.GetBufferAsync(uri);
      byte[] buff = WindowsRuntimeBufferExtensions.ToArray(ibuff);
      return buff;
    }

    private async Task<byte[]> PostWebData(Uri uri, byte[] data)
    {
      HttpClient client = new HttpClient();
      HttpBufferContent body = data != null ? new HttpBufferContent(WindowsRuntimeBufferExtensions.AsBuffer(data)) : (HttpBufferContent) null;
      HttpResponseMessage response = await client.PostAsync(uri, (IHttpContent) body);
      IBuffer ibuff = await response.get_Content().ReadAsBufferAsync();
      byte[] buff = WindowsRuntimeBufferExtensions.ToArray(ibuff);
      return buff;
    }

    private async Task<string> ReadLocalFileAsync(string filename)
    {
      StorageFile file = await ApplicationData.get_Current().get_LocalFolder().GetFileAsync(filename);
      string content = await FileIO.ReadTextAsync((IStorageFile) file);
      return content;
    }

    private async Task WriteLocalFileAsync(string filename, string content)
    {
      StorageFile file = await ApplicationData.get_Current().get_LocalFolder().CreateFileAsync(filename, (CreationCollisionOption) 1);
      await FileIO.WriteTextAsync((IStorageFile) file, content);
    }

    public async Task<string> GetWebString(Uri uri, bool bypassCahce)
    {
      byte[] buff = await this.GetWebData(uri, bypassCahce);
      string result = Encoding.UTF8.GetString(buff, 0, buff.Length);
      return result;
    }

    public async Task<string> PostWebString(Uri uri, byte[] data)
    {
      byte[] buff = await this.PostWebData(uri, data);
      string result = Encoding.UTF8.GetString(buff, 0, buff.Length);
      return result;
    }

    public string GetUserId()
    {
      try
      {
        return SettingsHelper.GetValue<string>("UID", (string) null);
      }
      catch
      {
        return (string) null;
      }
    }

    public string GetSecurityToken()
    {
      return SettingsHelper.GetValue<string>("X", (string) null);
    }

    public async Task<UserProfile> GetUserProfile()
    {
      string userId = this.GetUserId();
      string securityToken = this.GetSecurityToken();
      UserProfile userProfile;
      if (string.IsNullOrEmpty(userId))
      {
        string deviceId = DataContext.GetDeviceId();
        securityToken = Guid.NewGuid().ToString("N");
        userId = await this.GetWebString(new Uri("http://berlox.com/finance/api?action=registeruser&x=" + securityToken + "&deviceid=" + DataContext.UriEncode(deviceId) + DataContext.UrlRnd()), true);
        if (string.IsNullOrEmpty(userId) || userId.Length != 11)
        {
          userProfile = (UserProfile) null;
          goto label_8;
        }
        else
        {
          SettingsHelper.SetValue<string>("UID", userId);
          SettingsHelper.SetValue<string>("X", securityToken);
        }
      }
      byte[] buff = await this.GetWebData(new Uri("http://berlox.com/finance/api?action=getuserprofile&uid=" + userId + "&x=" + securityToken + DataContext.UrlRnd()), true);
      string json = Encoding.UTF8.GetString(buff, 0, buff.Length);
      UserProfile result = await Task.Factory.StartNew<UserProfile>((Func<UserProfile>) (() => JsonConvert.DeserializeObject<UserProfile>(json)));
      userProfile = result;
label_8:
      return userProfile;
    }

    public async Task SetUserPhone(string phone)
    {
      string userId = this.GetUserId();
      if (!string.IsNullOrEmpty(userId))
      {
        string str = await this.PostWebString(new Uri("http://berlox.com/finance/api?action=setuserphone&phone=" + DataContext.UriEncode(phone) + "&uid=" + userId + "&x=" + this.GetSecurityToken() + DataContext.UrlRnd()), (byte[]) null);
      }
    }

    public async Task ConfirmUserPhone(string code)
    {
      string userId = this.GetUserId();
      if (!string.IsNullOrEmpty(userId))
      {
        string str = await this.PostWebString(new Uri("http://berlox.com/finance/api?action=confirmuserphone&code=" + DataContext.UriEncode(code) + "&uid=" + userId + "&x=" + this.GetSecurityToken() + DataContext.UrlRnd()), (byte[]) null);
      }
    }

    public async Task SendNewPhoneConfirmationCode()
    {
      string userId = this.GetUserId();
      if (!string.IsNullOrEmpty(userId))
      {
        string str = await this.PostWebString(new Uri("http://berlox.com/finance/api?action=sendnewphoneconfirmationcode&uid=" + userId + "&x=" + this.GetSecurityToken() + DataContext.UrlRnd()), (byte[]) null);
      }
    }

    public async Task PublishUserDeal(MarketDeal deal)
    {
      if (deal != null)
      {
        string userId = this.GetUserId();
        if (!string.IsNullOrEmpty(userId))
        {
          string oldDealId = deal.DealId;
          if (!deal.IsActive)
            deal.DealId = (string) null;
          string json = await Task.Factory.StartNew<string>((Func<string>) (() => JsonConvert.SerializeObject((object) deal)));
          byte[] key = DataKey.GetCurrentKey();
          byte[] data = await Task.Factory.StartNew<byte[]>((Func<byte[]>) (() => new SimpleAES(key).Encrypt(json)));
          string dealId = await this.PostWebString(new Uri("http://berlox.com/finance/api?action=publishuserdeal&uid=" + userId + "&x=" + this.GetSecurityToken() + DataContext.UrlRnd()), data);
          if (!string.IsNullOrEmpty(dealId) && dealId.Length == 32)
          {
            deal.DealId = dealId;
            deal.Timestamp = DateTime.Now;
            List<MarketDeal> mydeals = await this.GetMyDealsAsync();
            if (!string.IsNullOrEmpty(oldDealId))
              mydeals.RemoveAll((Predicate<MarketDeal>) (d => d.DealId == oldDealId));
            mydeals.RemoveAll((Predicate<MarketDeal>) (d => d.DealId == dealId));
            mydeals.Add(deal);
            await this.SaveMyDealsAsync(mydeals);
          }
        }
      }
    }

    public async Task RemoveUserDeal(MarketDeal deal)
    {
      if (deal != null && !string.IsNullOrEmpty(deal.DealId))
      {
        string userId = this.GetUserId();
        if (!string.IsNullOrEmpty(userId))
        {
          if (deal.IsActive)
          {
            string result = await this.PostWebString(new Uri("http://berlox.com/finance/api?action=removeuserdeal&dealid=" + DataContext.UriEncode(deal.DealId) + "&uid=" + userId + "&x=" + this.GetSecurityToken() + DataContext.UrlRnd()), (byte[]) null);
            if (result != "OK")
              goto label_8;
          }
          List<MarketDeal> mydeals = await this.GetMyDealsAsync();
          mydeals.RemoveAll((Predicate<MarketDeal>) (d => d.DealId == deal.DealId));
          await this.SaveMyDealsAsync(mydeals);
        }
      }
label_8:;
    }

    public async Task<List<MarketDeal>> GetMyDealsAsync()
    {
      List<MarketDeal> list;
      try
      {
        string json = await this.ReadLocalFileAsync("mydeals.json");
        List<MarketDeal> result = await Task.Factory.StartNew<List<MarketDeal>>((Func<List<MarketDeal>>) (() => JsonConvert.DeserializeObject<List<MarketDeal>>(json)));
        list = result;
      }
      catch
      {
        list = new List<MarketDeal>();
      }
      return list;
    }

    private async Task SaveMyDealsAsync(List<MarketDeal> mydeals)
    {
      if (mydeals != null)
      {
        mydeals = Enumerable.ToList<MarketDeal>((IEnumerable<MarketDeal>) Enumerable.ThenBy<MarketDeal, DateTime>(Enumerable.ThenBy<MarketDeal, int>(Enumerable.OrderBy<MarketDeal, string>((IEnumerable<MarketDeal>) mydeals, (Func<MarketDeal, string>) (d => d.Currency)), (Func<MarketDeal, int>) (d => d.Type)), (Func<MarketDeal, DateTime>) (d => d.Timestamp)));
        string mydealsContent = await Task.Factory.StartNew<string>((Func<string>) (() => JsonConvert.SerializeObject((object) mydeals)));
        await this.WriteLocalFileAsync("mydeals.json", mydealsContent);
      }
    }

    private async Task SaveCityListAsync(MarketListing listing)
    {
      if (listing != null)
      {
        if (listing.Deals != null)
        {
          try
          {
            string[] cities = listing.Cities == null || listing.Cities.Count <= 0 ? Enumerable.ToArray<string>((IEnumerable<string>) Enumerable.OrderBy<string, string>(Enumerable.Distinct<string>(Enumerable.Select<MarketDeal, string>((IEnumerable<MarketDeal>) listing.Deals, (Func<MarketDeal, string>) (d => d.City))), (Func<string, string>) (x => x))) : listing.Cities.ToArray();
            if (cities.Length != 0)
            {
              string txt = string.Join("\r\n", cities);
              await this.WriteLocalFileAsync("cities.txt", txt);
            }
          }
          catch
          {
          }
        }
      }
    }

    public async Task<List<string>> GetCityListAsync()
    {
      List<string> list;
      try
      {
        string txt = await this.ReadLocalFileAsync("cities.txt");
        IEnumerable<string> lines = DataContext.ReadLines(txt);
        List<string> result = Enumerable.ToList<string>(lines);
        list = result;
      }
      catch
      {
        list = new List<string>()
        {
          "Киев"
        };
      }
      return list;
    }

    private static IEnumerable<string> ReadLines(string s)
    {
      using (StringReader stringReader = new StringReader(s))
      {
        string line;
        while ((line = stringReader.ReadLine()) != null)
          yield return line;
      }
    }

    private static string UrlRnd()
    {
      return "&r=" + (object) new Random().Next(999999);
    }

    private static string UriEncode(string text)
    {
      return Uri.EscapeDataString(text);
    }

    public static string GetDeviceId()
    {
      string str = string.Empty;
      try
      {
        IBuffer id = HardwareIdentification.GetPackageSpecificToken((IBuffer) null).get_Id();
        DataReader dataReader = DataReader.FromBuffer(id);
        byte[] numArray = new byte[(IntPtr) id.get_Length()];
        dataReader.ReadBytes(numArray);
        str = BitConverter.ToString(numArray).Replace("-", "");
      }
      catch
      {
      }
      return str;
    }
  }
}

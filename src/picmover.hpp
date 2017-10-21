#pragma once

#include "version.hpp"

#include <experimental/filesystem>
#include <vector>
#include <regex>
#include <string>
#include <map>
#include <algorithm>
#include <type_traits>

namespace picmover {
inline
namespace PICMOVER_VERSION_STR {
  namespace fs = std::experimental::filesystem;
  
  using Files = std::vector<fs::path>;
  using Corrections = std::vector<std::tuple<std::regex, std::string>>;

  struct RegexFilter{
    RegexFilter( std::regex regex ): m_regex(regex){}
    bool operator()( const fs::path& file ) const;
  private:
    std::regex m_regex;
  };

  class MakerAttribute {
  public:
    MakerAttribute( const Corrections& corrections = Corrections(),
                    const std::string& default_maker = "Unknown" );
    std::string operator()( const fs::path& file ) const;
  private:
    const Corrections& m_corrections;
    const std::string m_default_maker;
  };
  
  struct ModelAttribute {
    std::string operator()( const fs::path& file ) const;
  };
  
  struct DateAttribute {
    std::string operator()( const fs::path& file ) const;
  };

  /// If str matches any of the regexes in corrections it will replace
  /// it with the associated string.
  std::string correct( const std::string& str, const Corrections& corrections );

  /// Read in all files at specifed path.
  Files read( const fs::path& path );

  // Filter out based on operator
  template< typename Filter>
  Files filter( const Files& files, const Filter filter );

  /// Group by attributes
  template< typename Attribute>
  auto groupBy( const Files& files, const Attribute attribute ) ->
    std::map<std::decay_t<decltype( attribute(fs::path()) )>, Files>;

  // Copy files
  void copy( const Files& files, const fs::path& destination );


} // namespace vX_Y
} // namespace picmover


namespace picmover {
inline 
namespace PICMOVER_VERSION_STR {

  template< typename Filter>
  Files filter( const Files& files, Filter filter )
  {
    Files subset;
    std::copy_if(std::begin(files), std::end(files), std::back_inserter(subset), filter);
    return subset;
  }

  template< typename Attribute>
  auto groupBy( const Files& files, const Attribute attribute ) ->
    std::map<std::decay_t<decltype( attribute(fs::path()) )>, Files>
  {
    std::map<std::decay_t<decltype( attribute(fs::path()) )>, Files> groups;

    for( const fs::path& file : files )
      groups[ attribute( file ) ].emplace_back( file );

    return groups;
  }
}
}

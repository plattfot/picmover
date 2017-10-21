#include "picmover.hpp"

namespace picmover {
inline
namespace PICMOVER_VERSION_STR {

  Files read( const fs::path& path )
  {
    Files files;

    for( fs::directory_iterator it( path ), end; it != end; ++it )
      {
        if( it->status().type() == fs::file_type::regular )
          files.emplace_back( it->path() );
      }

    return files;
  }

  // Copy files
  void copy( const Files& files, const fs::path& destination )
  {
    // Make sure the path exist
    fs::create_directories( destination );

    for( const auto& file : files )
      fs::copy( file, destination );
  }

  auto RegexFilter::operator()( const fs::path& file ) const -> bool
  {
    return std::regex_search( file.string(), m_regex );
  }

} // namespace vX_Y
} // namespace picmover...
